from core.prompts import ACTION_TYPE_PROMPT, TRANSACTION_PROMPT, TRANSFER_PROMPT, FOREX_PROMPT, INVESTMENT_PROMPT, INCOME_PROMPT, EXPENSE_PROMPT
from integrations.providers.llm_akash import AkashLLMClient as LLMAgent
from integrations.spreadsheet.spreadsheet import GoogleSheetsClient as GSheetsClient
from integrations.supabase.supabase import SupabaseManager as SupaManager
import logging
from datetime import datetime
from models.action_type import ActionTypes
from models.forex import Forex
from models.investment import Investment
from models.transaction import Transaction
from models.transfer import Transfer
import pytz
from typing import Union, Optional, List, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class RequestLLMModel(BaseModel):
    prompt: str
    output_model: Type[BaseModel]

class ProcessingResult(BaseModel):
    """
    Represents the result of processing and saving a data object.
    """
    data_object: Optional[Union[Forex, Investment, Transaction, Transfer]] = None
    saved_to_spreadsheet: bool = False
    saved_to_database: bool = False
    error: Optional[str] = None

class LLMProcessor:
    """
    Processor to handle interaction with the LLM client and extract structured data
    from the LLM's response.
    """

    def __init__(self):
        """
        Initializes the LLMProcessor with instances of the LLM, spreadsheet, and
        database clients. Logs the initialization.
        """
        self.llm_client = LLMAgent()
        self.spreadsheet_client = GSheetsClient()
        self.supabase_client = SupaManager()
        logger.info("LLMProcessor initialized.")

    async def process_content(self, content: str) -> List[ProcessingResult]:
        """
        Processes the input content by determining the action type using the LLM,
        generating responses for each required step, and saving the data.

        Args:
            content: The input string to be processed.

        Returns:
            A list of ProcessingResult objects, each containing the processed data
            and the status of saving to spreadsheet and database.
        """
        logger.info(f"Processing content: '{content}'")
        processing_results: List[ProcessingResult] = []

        try:
            action_type = self.determine_action_type(content)
            if not action_type:
                logger.warning(f"Could not determine action type for content: '{content}'.")
                processing_results.append(ProcessingResult(error="No se pudo determinar una accion para registrar en base al mensaje"))
                return processing_results

            llm_request_models = await self._process_action(content, action_type)
            if not llm_request_models:
                logger.warning(f"Failed to create LLM request models for action: '{action_type.value}'.")
                processing_results.append(ProcessingResult(error=f"Se identifico la accion '{action_type.value}' pero no fue posible procesar el mensaje."))
                return processing_results

            llm_responses: List[ProcessingResult] = []
            for request in llm_request_models:
                try:
                    response = self.llm_client.generate_response(
                        prompt=request.prompt, output=request.output_model
                    )
                    llm_responses.append(ProcessingResult(data_object=response))
                except Exception as e:
                    logger.error(f"Error calling LLM for prompt: '{request.output_model.__name__}': '{e}'", exc_info=True)
                    llm_responses.append(ProcessingResult(error=f'Ocurrio un error procesando la {request.output_model.__name__}'))

            current_datetime = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
            for response in llm_responses:
                if response:
                    response.data_object.date = current_datetime
                    response.saved_to_spreadsheet= self._save_to_spreadsheet(response.data_object)
                    response.saved_to_database= await self._save_to_database(response.data_object)
                    processing_results.append(response)
                    logger.info(f"Processed: {response.model_dump_json()}")
                else:
                    processing_results.append(ProcessingResult(error="LLM returned no data"))

        except Exception as e:
            logger.error(f"An unexpected error occurred during content processing: '{e}'", exc_info=True)
            processing_results.append(ProcessingResult(error=f"Algo sucedio. No pudimos procesar el mensaje :("))

        return processing_results

    def determine_action_type(self, content: str) -> Optional[ActionTypes]:
        """
        Determines the action type from the input content using the LLM.
        """
        prompt = ACTION_TYPE_PROMPT.format(content=content)
        action = self.llm_client.determinate_action(prompt)
        logger.debug(f"Determined action type: '{action.action}' for content: '{content}'.")
        return action.action

    async def _process_action(self, content: str, action_type: ActionTypes) -> Optional[List[RequestLLMModel]]:
        """
        Determines the necessary LLM calls based on the action type and returns
        a list of RequestLLMModel objects.

        Args:
            content: The input string.
            action_type: The determined ActionTypes.

        Returns:
            A list of RequestLLMModel objects, or None if no requests are needed.
        """
        if action_type == ActionTypes.TRANSFER:
            return self._prepare_transfer_requests(content)
        elif action_type == ActionTypes.EXCHANGE:
            return self._prepare_exchange_requests(content)
        elif action_type == ActionTypes.TRANSACTION:
            return self._prepare_transaction_requests(content)
        elif action_type == ActionTypes.INVESTMENT:
            return self._prepare_investment_requests(content)

    def _prepare_transfer_requests(self, content: str) -> List[RequestLLMModel]:
        """Prepares LLM request models for a Transfer action."""
        reason = "En la transferencia pudo existir un fee/comision si el monto origen es distinto al monto destino. El fee seria monto origen - monto destino"

        return [
            RequestLLMModel(
                prompt=self._get_prompt(TRANSFER_PROMPT, content),
                output_model=Transfer
            ),
            RequestLLMModel(
                prompt=self._get_prompt(EXPENSE_PROMPT, content, reason=reason),
                output_model=Transaction
            ),
        ]

    def _prepare_exchange_requests(self, content: str) -> List[RequestLLMModel]:
        """Prepares LLM request models for an Exchange action."""
        reason_transfer = "De este cambio de divisas se redujo la cantidad de plata en la billetera origen por lo que se deberia insertar una transferencia con wallet_to=None y final ammout=0"
        reason_income = "De este cambio de divisas se obtuvo un monto de pesos argentinos por lo que se considera un ingreso en pesos argentinos. Hacer multiplicacion de cantidad de dolares por precio dolar si es necesario."
        return [
            RequestLLMModel(
                prompt=self._get_prompt(FOREX_PROMPT, content),
                output_model=Forex
            ),
            RequestLLMModel(
                prompt=self._get_prompt(INCOME_PROMPT, content, reason=reason_income),
                output_model=Transaction
            ),
            RequestLLMModel(
                prompt=self._get_prompt(TRANSFER_PROMPT, content, reason=reason_transfer),
                output_model=Transfer
            ),
        ]

    def _prepare_transaction_requests(self, content: str) -> List[RequestLLMModel]:
        """Prepares LLM request models for a Transaction action."""
        return [
            RequestLLMModel(
                prompt=self._get_prompt(TRANSACTION_PROMPT, content),
                output_model=Transaction
            )
        ]

    def _prepare_investment_requests(self, content: str) -> List[RequestLLMModel]:
        """Prepares LLM request models for an Investment action."""
        return [
            RequestLLMModel(
                prompt=self._get_prompt(INVESTMENT_PROMPT, content),
                output_model=Investment
            )
        ]

    def _get_prompt(self, promp: str, content: str, reason: Optional[str] = None) -> str:
        """
        Determines the appropriate prompt based on the action type and an optional reason.

        Args:
            promp: promp string.
            content: The input content to be formatted into the prompt.
            reason: An optional reason to include in the prompt. Defaults to None.

        Returns:
            The formatted prompt.
        """
        return promp.format(content=content, reason=reason if reason else "")

    def _save_to_spreadsheet(self, data: Union[Forex, Investment, Transaction, Transfer]) -> bool:
        """
        Saves the processed data to the Google Sheets spreadsheet.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            logger.info(f"Saving data to spreadsheet: '{data.__class__.__name__}'")
            data.save_to_sheet(self.spreadsheet_client)
            logger.info(f"Successfully saved to spreadsheet.")
            return True
        except Exception as e:
            logger.error(f"Error saving data to spreadsheet: '{e}'", exc_info=True)
            return False

    async def _save_to_database(self, data: Union[Forex, Investment, Transaction, Transfer]) -> bool:
        """
        Saves the processed data to the Supabase database.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            logger.info(f"Saving data to database: '{data.__class__.__name__}'")
            await data.save_to_database(self.supabase_client)
            logger.info(f"Successfully saved to database.")
            return True
        except Exception as e:
            logger.error(f"Error saving data to database: '{e}'", exc_info=True)
            return False
from dataclasses import dataclass

from src.models.invoice import Invoice


@dataclass
class BillingSyncResult:
    external_reference: str
    status: str


class MockBillingAdapter:
    """Local billing boundary used until the external payments app is available."""

    def create_invoice(self, invoice: Invoice) -> BillingSyncResult:
        return BillingSyncResult(
            external_reference=f"mock-patas-{invoice.id}",
            status="sent",
        )

    def get_status(self, external_reference: str) -> str:
        return "sent"


billing_adapter = MockBillingAdapter()

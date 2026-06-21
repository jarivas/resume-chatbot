import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Certificate
from app.models import Certificate as CertificateItem
from app.services import CertificateService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> CertificateService:
    raise NotImplementedError("Resume service dependency not implemented")


class CertificateCreate(BaseModel):
    name: str
    date: str | None = None
    url: str | None = None
    issuer: str | None = None


class CertificateUpdate(BaseModel):
    name: str | None = None
    date: str | None = None
    url: str | None = None
    issuer: str | None = None


class CertificateResponse(BaseModel):
    id: str
    name: str | None
    date: str | None
    url: str | None
    issuer: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_certificate(cls, certificate: Certificate) -> "CertificateResponse":
        return cls(
            id=certificate.id,
            name=certificate.name,
            date=certificate.date,
            url=certificate.url,
            issuer=certificate.issuer,
            created_at=certificate.created_at.isoformat() if certificate.created_at else "",
            updated_at=certificate.updated_at.isoformat() if certificate.updated_at else "",
        )


router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post(
    "",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create certificate entry",
    description="Creates a new certificate entry and synchronizes it with vector database.",
)
async def create_certificate(
    certificate_data: CertificateCreate,
    service: CertificateService = Depends(get_resume_service),
) -> Certificate:
    logger.info(
        "Creating certificate entry endpoint",
        name=certificate_data.name,
        issuer=certificate_data.issuer,
    )

    certificate_item = CertificateItem(
        name=certificate_data.name,
        date=certificate_data.date,
        url=certificate_data.url,
        issuer=certificate_data.issuer,
    )

    try:
        created_certificate = await service.create_certificate(certificate_item)
        logger.info("Certificate entry created successfully", certificate_id=created_certificate.id)
        return CertificateResponse.from_certificate(created_certificate)
    except Exception as e:
        logger.error(
            "Failed to create certificate entry", error=str(e), name=certificate_data.name
)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create certificate entry: {str(e)}",
        )


@router.get(
    "/{certificate_id}",
    response_model=CertificateResponse,
    summary="Get certificate entry by ID",
    description="Retrieves a specific certificate entry by its unique identifier.",
)
async def get_certificate(
    certificate_id: str,
    service: CertificateService = Depends(get_resume_service),
) -> Certificate:
    logger.info("Retrieving certificate entry", certificate_id=certificate_id)
    certificate = await service.get_certificate(certificate_id)
    if not certificate:
        logger.warning("Certificate entry not found", certificate_id=certificate_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate entry with id {certificate_id} not found",
        )
    return CertificateResponse.from_certificate(certificate)


@router.get(
    "",
    response_model=list[CertificateResponse],
    summary="Get all certificate entries",
    description="Retrieves all certificate entries from database.",
)
async def get_all_certificates(
    service: CertificateService = Depends(get_resume_service),
) -> list[CertificateResponse]:
    logger.info("Retrieving all certificate entries")
    certificates = await service.get_all_certificates()
    logger.info("Certificate entries retrieved", count=len(certificates))
    return [CertificateResponse.from_certificate(certificate) for certificate in certificates]


@router.patch(
    "/{certificate_id}",
    response_model=CertificateResponse,
    summary="Update certificate entry",
    description="Updates specific fields of a certificate entry and synchronizes changes with vector database.",
)
async def update_certificate(
    certificate_id: str,
    certificate_update: CertificateUpdate,
    service: CertificateService = Depends(get_resume_service),
) -> Certificate:
    logger.info("Updating certificate entry", certificate_id=certificate_id)
    existing_certificate = await service.get_certificate(certificate_id)
    if not existing_certificate:
        logger.warning("Cannot update non-existent certificate entry", certificate_id=certificate_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate entry with id {certificate_id} not found",
        )

    updated_data = CertificateItem(
        name=certificate_update.name if certificate_update.name is not None else existing_certificate.name,
        date=certificate_update.date if certificate_update.date is not None else existing_certificate.date,
        url=certificate_update.url if certificate_update.url is not None else existing_certificate.url,
        issuer=certificate_update.issuer if certificate_update.issuer is not None else existing_certificate.issuer,
    )

    updated_certificate = await service.update_certificate(certificate_id, updated_data)
    logger.info("Certificate entry updated successfully", certificate_id=certificate_id)
    return CertificateResponse.from_certificate(updated_certificate)


@router.delete(
    "/{certificate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete certificate entry",
    description="Deletes a certificate entry from both SQLite and ChromaDB.",
)
async def delete_certificate(
    certificate_id: str,
    service: CertificateService = Depends(get_resume_service),
):
    logger.info("Deleting certificate entry", certificate_id=certificate_id)
    deleted = await service.delete_certificate(certificate_id)
    if not deleted:
        logger.warning("Cannot delete non-existent certificate entry", certificate_id=certificate_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate entry with id {certificate_id} not found",
        )
    logger.info("Certificate entry deleted successfully", certificate_id=certificate_id)
    return None

import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Certificate
from app.models import Certificate as CertificateItem

logger = structlog.get_logger(__name__)


class CertificateService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_certificate(self, certificate_data: CertificateItem) -> Certificate:
        logger.info("Creating certificate entry", name=certificate_data.name)

        certificate = Certificate(
            name=certificate_data.name,
            date=certificate_data.date,
            url=str(certificate_data.url) if certificate_data.url else None,
            issuer=certificate_data.issuer,
        )

        try:
            self.session.add(certificate)
            await self.session.commit()
            await self.session.refresh(certificate)
            await self._index_certificate_in_chroma(certificate)
            logger.info("Certificate entry created successfully", certificate_id=certificate.id)
            return certificate
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(certificate)
            logger.error(
                "Failed to create certificate entry", error=str(e), name=certificate_data.name
            )
            raise

    async def get_certificate(self, certificate_id: str) -> Certificate | None:
        logger.info("Retrieving certificate entry", certificate_id=certificate_id)
        result = await self.session.execute(select(Certificate).where(Certificate.id == certificate_id))
        certificate = result.scalar_one_or_none()
        if certificate:
            logger.info("Certificate entry found", certificate_id=certificate_id)
        else:
            logger.warning("Certificate entry not found", certificate_id=certificate_id)
        return certificate

    async def get_all_certificates(self) -> list[Certificate]:
        logger.info("Retrieving all certificate entries")
        result = await self.session.execute(select(Certificate))
        certificate_entries = list(result.scalars().all())
        logger.info("Retrieved certificate entries", count=len(certificate_entries))
        return certificate_entries

    async def update_certificate(self, certificate_id: str, certificate_data: CertificateItem) -> Certificate | None:
        logger.info("Updating certificate entry", certificate_id=certificate_id)
        certificate = await self.get_certificate(certificate_id)
        if not certificate:
            logger.warning("Cannot update non-existent certificate entry", certificate_id=certificate_id)
            return None

        certificate.name = certificate_data.name
        certificate.date = certificate_data.date
        certificate.url = str(certificate_data.url) if certificate_data.url else None
        certificate.issuer = certificate_data.issuer

        try:
            await self.session.commit()
            await self.session.refresh(certificate)
            await self._index_certificate_in_chroma(certificate)
            logger.info("Certificate entry updated successfully", certificate_id=certificate_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update certificate entry", certificate_id=certificate_id, error=str(e))
            raise

        return certificate

    async def delete_certificate(self, certificate_id: str) -> bool:
        logger.info("Deleting certificate entry", certificate_id=certificate_id)
        certificate = await self.get_certificate(certificate_id)
        if not certificate:
            logger.warning("Cannot delete non-existent certificate entry", certificate_id=certificate_id)
            return False

        await self._delete_from_chroma(certificate_id, "certificate")
        await self.session.delete(certificate)
        await self.session.commit()
        logger.info("Certificate entry deleted successfully", certificate_id=certificate_id)
        return True

    async def _index_certificate_in_chroma(self, certificate: Certificate) -> None:
        logger.info("Indexing certificate entry in ChromaDB", certificate_id=certificate.id)

        parts = []

        if certificate.name:
            parts.append(f"Certificate: {certificate.name}")
        if certificate.issuer:
            parts.append(f"Issuer: {certificate.issuer}")
        if certificate.date:
            parts.append(f"Date: {certificate.date}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "certificate",
            "entity_id": certificate.id,
            "name": certificate.name or "",
            "issuer": certificate.issuer or "",
            "created_at": certificate.created_at.isoformat() if certificate.created_at else "",
            "updated_at": certificate.updated_at.isoformat() if certificate.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"certificate_{certificate.id}"],
        )
        logger.info("Certificate entry indexed successfully", certificate_id=certificate.id)

    async def _delete_from_chroma(self, entity_id: str, entity_type: str) -> None:
        logger.info(
            "Deleting entry from ChromaDB", entity_id=entity_id, entity_type=entity_type
        )
        await self.chroma_collection.adelete(ids=[f"{entity_type}_{entity_id}"])
        logger.info(
            "Entry deleted from ChromaDB successfully",
            entity_id=entity_id,
            entity_type=entity_type,
        )

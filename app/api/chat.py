import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.services.cv_service import ResumeService

logger = structlog.get_logger(__name__)


class ChatRequest(BaseModel):
    question: str
    model: str = "gpt-4o-mini"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    context_used: bool


async def get_resume_service() -> ResumeService:
    raise NotImplementedError("Resume service dependency not implemented")


router = APIRouter(prefix="/chat", tags=["chat"])


SYSTEM_PROMPT = """You are an expert professional assistant specializing in resume analysis and career guidance. 
Your role is to answer questions about a candidate's professional background based on the provided context from their resume.

Context information:
{context}

Guidelines:
- Use only the information provided in the context to answer questions
- If the context doesn't contain relevant information, clearly state that the information is not available in the resume
- Be professional, concise, and factual
- When discussing work experience, mention specific achievements, technologies, and timeframes when available
- When discussing education, include degrees, institutions, and relevant coursework
- When discussing skills, indicate proficiency level and practical applications
- If asked about information not present in the context, suggest what additional information would be helpful

User question: {question}

Provide a thorough and professional response based on the available context."""


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with resume",
    description="Ask questions about the resume and get AI-powered answers using RAG.",
)
async def chat_with_resume(
    request: ChatRequest,
    service: ResumeService = Depends(get_resume_service),
) -> ChatResponse:
    logger.info("Processing chat request", question=request.question[:50])

    try:
        retriever = service.chroma_collection.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

        relevant_docs = await retriever.aget_relevant_documents(request.question)

        if not relevant_docs:
            logger.warning("No relevant documents found in vector store")
            return ChatResponse(
                answer="I don't have any information in the resume to answer your question. The resume database appears to be empty or doesn't contain relevant content.",
                sources=[],
                context_used=False,
            )

        prompt = PromptTemplate(
            template=SYSTEM_PROMPT,
            input_variables=["context", "question"],
        )

        llm = ChatOpenAI(
            model=request.model,
            temperature=0.7,
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
        )

        response = await qa_chain.ainvoke({"query": request.question})

        sources = [
            f"{doc.metadata.get('entity_type', 'unknown')} - {doc.metadata.get('entity_id', 'unknown')}"
            for doc in relevant_docs
        ]

        logger.info("Chat response generated successfully", sources_count=len(sources))
        return ChatResponse(
            answer=response.get("result", str(response)),
            sources=sources,
            context_used=True,
        )

    except Exception as e:
        if "empty" in str(e).lower() or "no documents" in str(e).lower():
            logger.warning("Empty vector store detected")
            return ChatResponse(
                answer="The resume database appears to be empty. Please add work experience, education, or skills to the resume first.",
                sources=[],
                context_used=False,
            )

        logger.error("Error processing chat request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your question: {str(e)}",
        )

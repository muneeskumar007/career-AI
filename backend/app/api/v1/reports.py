from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.common import SuccessResponse
from app.schemas.report import PerformanceReportResponse, ProgressHistoryResponse
from app.schemas.user import UserResponse
from app.services.report.pdf_export import render_report_pdf
from app.services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["Performance Report"])


@router.get("", response_model=SuccessResponse[PerformanceReportResponse])
async def get_report(
    resume_id: str | None = Query(default=None),
    interview_id: str | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ReportService(db)
    result = await service.generate(current_user.id, resume_id, interview_id)
    return SuccessResponse(data=result)


@router.get("/progress", response_model=SuccessResponse[ProgressHistoryResponse])
async def get_progress_history(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ReportService(db)
    result = await service.progress_history(current_user.id)
    return SuccessResponse(data=result)


@router.get("/export-pdf")
async def export_report_pdf(
    resume_id: str | None = Query(default=None),
    interview_id: str | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ReportService(db)
    report = await service.generate(current_user.id, resume_id, interview_id)
    pdf_bytes = render_report_pdf(report, current_user.name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=careerai-performance-report.pdf"},
    )

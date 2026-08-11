import api from "@/services/api";

export async function getReport(resumeId, interviewId) {
  const params = new URLSearchParams();
  if (resumeId) params.set("resume_id", resumeId);
  if (interviewId) params.set("interview_id", interviewId);
  const { data } = await api.get(`/report?${params.toString()}`);
  return data.data;
}

export async function getProgressHistory() {
  const { data } = await api.get("/report/progress");
  return data.data;
}

export async function downloadReportPdf(resumeId, interviewId) {
  const params = new URLSearchParams();
  if (resumeId) params.set("resume_id", resumeId);
  if (interviewId) params.set("interview_id", interviewId);

  // A plain <a href> or window.open wouldn't carry the Bearer token this
  // endpoint requires — fetch through the authenticated axios instance as a
  // blob instead, then trigger the download from that.
  const response = await api.get(`/report/export-pdf?${params.toString()}`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "careerai-performance-report.pdf";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function getDashboard() {
  const { data } = await api.get("/dashboard");
  return data.data;
}

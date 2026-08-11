import api from "@/services/api";

export async function createJobDescription({ title, company, rawText }) {
  const { data } = await api.post("/job", { title, company, raw_text: rawText });
  return data.data;
}

export async function listJobDescriptions() {
  const { data } = await api.get("/job");
  return data.data;
}

export async function compareATS(resumeId, jobDescriptionId) {
  const { data } = await api.post("/ats/compare", { resume_id: resumeId, job_description_id: jobDescriptionId });
  return data.data;
}

export async function getATSResult(resumeId, jobDescriptionId) {
  const { data } = await api.get(`/ats/${resumeId}/${jobDescriptionId}`);
  return data.data;
}

export async function getSkillGap(resumeId, jobDescriptionId) {
  const { data } = await api.get(`/skill-gap/${resumeId}/${jobDescriptionId}`);
  return data.data;
}

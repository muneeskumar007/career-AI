import api from "@/services/api";

export async function improveResume(resumeId, targetRole) {
  const { data } = await api.post(`/resume/${resumeId}/improve`, { target_role: targetRole || null });
  return data.data;
}

export async function generateQuestions(resumeId, jobDescriptionId, difficulty) {
  const { data } = await api.post("/interview/questions", {
    resume_id: resumeId, job_description_id: jobDescriptionId || null, difficulty,
  });
  return data.data;
}

export async function startInterview(resumeId, jobDescriptionId, mode) {
  const { data } = await api.post("/interview/start", {
    resume_id: resumeId, job_description_id: jobDescriptionId || null, mode,
  });
  return data.data;
}

export async function getCurrentQuestion(interviewId) {
  const { data } = await api.get(`/interview/${interviewId}/current-question`);
  return data.data;
}

export async function submitAnswer(interviewId, question, category, answerText) {
  const { data } = await api.post(`/interview/${interviewId}/answer`, {
    question, category, answer_text: answerText,
  });
  return data.data;
}

export async function submitAudioAnswer(interviewId, question, category, audioBlob) {
  const formData = new FormData();
  formData.append("question", question);
  formData.append("category", category);
  formData.append("file", audioBlob, "answer.webm");
  const { data } = await api.post(`/interview/${interviewId}/answer/audio`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.data;
}

export async function submitVideoAnswer(interviewId, question, category, videoBlob) {
  const formData = new FormData();
  formData.append("question", question);
  formData.append("category", category);
  formData.append("file", videoBlob, "answer.webm");
  const { data } = await api.post(`/interview/${interviewId}/answer/video`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.data;
}

export async function getInterview(interviewId) {
  const { data } = await api.get(`/interview/${interviewId}`);
  return data.data;
}

export async function listAnswers(interviewId) {
  const { data } = await api.get(`/interview/${interviewId}/answers`);
  return data.data;
}

export async function listInterviews() {
  const { data } = await api.get("/interview");
  return data.data;
}

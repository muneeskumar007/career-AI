import api from "@/services/api";

export async function uploadResume(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/resume/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });
  return data.data;
}

export async function listResumes() {
  const { data } = await api.get("/resume");
  return data.data;
}

export async function getResume(resumeId) {
  const { data } = await api.get(`/resume/${resumeId}`);
  return data.data;
}

export async function deleteResume(resumeId) {
  await api.delete(`/resume/${resumeId}`);
}

export async function parseResume(resumeId) {
  const { data } = await api.post(`/resume/${resumeId}/parse`);
  return data.data;
}

export async function getResumeAnalysis(resumeId) {
  const { data } = await api.get(`/resume/${resumeId}/analysis`);
  return data.data;
}

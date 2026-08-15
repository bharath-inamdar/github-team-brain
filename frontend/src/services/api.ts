import axios from "axios";

const TOKEN_STORAGE_KEY = "teambrain_access_token";

export const AUTH_UNAUTHORIZED_EVENT = "teambrain:unauthorized";

console.log("TeamBrain API configuration:");
console.log(
  "API base URL:",
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1",
);

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAccessToken();
      window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
    }

    return Promise.reject(error);
  },
);

export interface AuthUser {
  id: number;
  email: string;
  username: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface RegisterPayload {
  email: string;
  password: string;
  username?: string;
}

export async function register(payload: RegisterPayload) {
  const response = await api.post<AuthResponse>(
    "/auth/register",
    payload,
  );

  return response.data;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const response = await api.post<AuthResponse>(
    "/auth/login",
    body,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    },
  );

  return response.data;
}

export async function getMe() {
  const response = await api.get<AuthUser>("/auth/me");

  return response.data;
}

export interface Repository {
  id: number;
  owner: string;
  name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  default_branch: string;
}

export interface DashboardOverview {
  repositories: number;
  issues: number;
  pull_requests: number;
  reviews: number;
  review_comments: number;
  summary_ready: boolean;
}

export interface ImportRepositoryResponse {
  success: boolean;
  message: string;
  repository: Repository;
}

export interface ImportStepResponse {
  message: string;
  imported_count: number;
}

export interface SourceCitation {
  citation_id: number;
  text: string;
  source_type: string;
  reviewer: string | null;
  state: string | null;
  path: string | null;
  line: number | null;
  pull_request_id: number | null;
  repository_id: number | null;
}

export interface AskRepositoryResponse {
  question: string;
  answer: string;
  sources: SourceCitation[];
}

export interface RepositorySummaryResponse {
  total_reviews: number;
  summary: string;
}

export interface IndexResponse {
  total_reviews: number;
  total_review_comments: number;
  indexed: number;
  indexed_reviews: number;
  indexed_review_comments: number;
  skipped_empty: number;
  skipped_short: number;
  skipped_bot: number;
  skipped_existing: number;
}

export async function getDashboardOverview() {
  const response = await api.get<DashboardOverview>(
    "/dashboard/overview",
  );

  return response.data;
}

export async function getRepositories() {
  const response = await api.get<Repository[]>(
    "/repositories",
    {
      params: {
        limit: 100,
      },
    },
  );

  return response.data;
}

export async function importRepository(url: string) {
  const response = await api.post<ImportRepositoryResponse>(
    "/repositories/import",
    {
      url,
    },
  );

  return response.data;
}

export async function importPullRequests(
  owner: string,
  repo: string,
) {
  const response = await api.post<ImportStepResponse>(
    `/repositories/import/${owner}/${repo}/pull-requests`,
  );

  return response.data;
}

export async function importReviews(
  owner: string,
  repo: string,
) {
  const response = await api.post<ImportStepResponse>(
    `/repositories/import/${owner}/${repo}/reviews`,
  );

  return response.data;
}

export async function importReviewComments(
  owner: string,
  repo: string,
) {
  const response = await api.post<ImportStepResponse>(
    `/repositories/import/${owner}/${repo}/review-comments`,
  );

  return response.data;
}

export async function indexReviewKnowledge() {
  const response = await api.post<IndexResponse>(
    "/ai/index-all-reviews",
  );

  return response.data;
}

export async function askRepository(
  question: string,
  repositoryId?: number,
) {
  const response = await api.get<AskRepositoryResponse>(
    "/ai/ask",
    {
      params: {
        question,
        repository_id: repositoryId,
      },
    },
  );

  return response.data;
}

export async function generateRepositorySummary(
  repositoryId?: number,
) {
  const response = await api.get<RepositorySummaryResponse>(
    "/ai/repository-summary",
    {
      params: {
        repository_id: repositoryId,
      },
    },
  );

  return response.data;
}

export default api;

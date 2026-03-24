import { api } from "./api";
import { mockApi } from "./api-mock";
import type { ApiClient } from "./api";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export const apiClient: ApiClient = USE_MOCKS ? mockApi : api;

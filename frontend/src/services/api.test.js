import { API_BASE_URL, apiClient } from "./api.js";

describe("apiClient", () => {
  it("uses the configured base URL", () => {
    expect(apiClient.defaults.baseURL).toBe(API_BASE_URL);
    expect(API_BASE_URL).toMatch(/^https?:\/\//);
  });
});

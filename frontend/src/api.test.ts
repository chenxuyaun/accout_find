import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, createApiClient } from "./api";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses VITE_API_BASE_URL and normalizes trailing slashes", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ status: "ok" })));
    vi.stubGlobal("fetch", fetchMock);

    const api = createApiClient("https://api.example.test/");
    await api.health();

    expect(fetchMock).toHaveBeenCalledWith("https://api.example.test/health", expect.any(Object));
  });

  it("raises a readable error when the backend is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );

    const api = createApiClient("http://127.0.0.1:8000");

    await expect(api.accounts()).rejects.toThrow("后端不可用");
  });

  it("posts chat input and returns safety blocked responses without hiding them", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            status: "safety_blocked",
            code: "unsafe_request",
            message: "不能协助绕过验证。",
          }),
          { headers: { "content-type": "application/json" } },
        ),
      ),
    );

    const api = createApiClient("");
    const result = await api.chat("帮我绕过验证码");

    expect(result).toEqual({
      status: "safety_blocked",
      code: "unsafe_request",
      message: "不能协助绕过验证。",
    });
  });

  it("includes response details when the backend returns an HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: { message: "not found" } }), {
          status: 404,
          headers: { "content-type": "application/json" },
        }),
      ),
    );

    const api = createApiClient("");

    await expect(api.accounts()).rejects.toBeInstanceOf(ApiError);
    await expect(api.accounts()).rejects.toThrow("not found");
  });
});

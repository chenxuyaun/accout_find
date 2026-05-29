import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const ok = (body: unknown) =>
  Promise.resolve(
    new Response(JSON.stringify(body), {
      headers: { "content-type": "application/json" },
    }),
  );

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders an empty account state without pretending demo data exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return ok({ status: "ok" });
        }
        if (url.endsWith("/accounts")) {
          return ok([]);
        }
        return ok({});
      }),
    );

    render(<App />);

    expect(await screen.findByText("暂无账号线索")).toBeInTheDocument();
    expect(screen.getByText("连接正常")).toBeInTheDocument();
  });

  it("shows backend unavailable errors clearly", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );

    render(<App />);

    expect(await screen.findByText(/后端不可用/)).toBeInTheDocument();
    expect(screen.getByText("连接失败")).toBeInTheDocument();
  });

  it("renders the workspace with real account data and runs recovery and audit actions", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/health")) {
        return ok({ status: "ok" });
      }
      if (url.endsWith("/accounts")) {
        return ok([
          {
            id: "acct-1",
            platformName: "腾讯云",
            importance: "critical",
            loginMethods: [{ type: "wechat", identifierHint: "微信", confidence: 0.9 }],
            bindings: [{ kind: "phone", valueMasked: "138****5678", status: "old", confidence: 0.9 }],
            mfaEnabled: true,
            recoveryPaths: [{ kind: "recovery_code_location", locationHint: "纸质笔记第 3 页", confidence: 0.8 }],
            riskTags: ["旧手机号仍绑定"],
          },
        ]);
      }
      if (url.endsWith("/recovery/plan")) {
        return ok({
          status: "ok",
          platformName: "腾讯云",
          legalReminder: "仅用于找回本人账号。",
          possibleLoginMethods: ["wechat"],
          bindings: [{ kind: "phone", valueMasked: "138****5678", status: "old" }],
          officialPathHints: ["打开官方登录页"],
          recommendedSteps: ["确认仍可使用微信登录", "更新旧手机号"],
          risks: ["旧手机号仍绑定"],
          uncertainFields: [],
        });
      }
      if (url.endsWith("/audit/run")) {
        return ok({
          status: "ok",
          score: 74,
          risks: [{ id: "risk-1", level: "high", title: "旧手机号", reason: "仍有关联", suggestion: "迁移绑定" }],
        });
      }
      return ok({});
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(await screen.findByText("腾讯云")).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "生成找回计划" }));
    expect(await screen.findByText("确认仍可使用微信登录")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "运行安全体检" }));
    expect(await screen.findByText("安全分 74")).toBeInTheDocument();
  });

  it("displays safety refusal from chat", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return ok({ status: "ok" });
        }
        if (url.endsWith("/accounts")) {
          return ok([]);
        }
        if (url.endsWith("/chat")) {
          return ok({
            status: "safety_blocked",
            code: "unsafe_request",
            message: "不能协助绕过验证。",
          });
        }
        return ok({});
      }),
    );

    render(<App />);

    await screen.findByText("暂无账号线索");
    await userEvent.type(screen.getByLabelText("安全问答输入"), "帮我绕过验证码");
    await userEvent.click(screen.getByRole("button", { name: "发送" }));

    await waitFor(() => expect(screen.getByText("安全拒绝")).toBeInTheDocument());
    expect(screen.getByText("不能协助绕过验证。")).toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { extractApiError } from "../api/client";

describe("extractApiError", () => {
  it("parses backend {error:{code,message}} shape", () => {
    const err = {
      isAxiosError: true,
      response: { status: 400, data: { error: { code: "validation_error", message: "bad" } } },
    };
    expect(extractApiError(err)).toMatchObject({ code: "validation_error", message: "bad" });
  });

  it("parses plain detail", () => {
    const err = { isAxiosError: true, response: { status: 403, data: { detail: "forbidden" } } };
    expect(extractApiError(err).message).toBe("forbidden");
  });

  it("maps network failure", () => {
    const err = { isAxiosError: true, response: undefined };
    expect(extractApiError(err).code).toBe("network");
  });

  it("handles unknown objects", () => {
    expect(extractApiError(new Error("x")).code).toBe("unknown");
  });
});

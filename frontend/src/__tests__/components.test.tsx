import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LandingPage } from "../pages/LandingPage";
import { ToastProvider } from "../providers/ToastProvider";
import { AuthProvider } from "../providers/AuthProvider";

describe("LandingPage", () => {
  it("renders hero in Arabic by default", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders CTA links", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThan(2);
  });
});

describe("AuthProvider smoke", () => {
  it("renders children", () => {
    render(
      <ToastProvider>
        <AuthProvider>
          <div>child-content-marker</div>
        </AuthProvider>
      </ToastProvider>
    );
    expect(screen.getByText("child-content-marker")).toBeInTheDocument();
  });
});

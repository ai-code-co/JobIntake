import type { ReactNode } from "react";

export interface PageSidebarSection {
  id: string;
  label: string;
}

export interface PageSidebarProps {
  /** Short label above the title (e.g. "Operations Portal") */
  badge?: string;
  /** Main heading in the sidebar */
  title: string;
  /** Description below the title */
  subtitle?: string;
  /** List of sections for in-page navigation */
  sections: PageSidebarSection[];
  /** Currently active section id (matches section.id) */
  currentSection: string;
  /** Called when user clicks a section link */
  onSectionChange: (id: string) => void;
  /** Optional progress: percent 0–100 and optional label (e.g. "5 important fields completed") */
  progress?: { percent: number; label?: string };
  /** Optional custom node below section list (replaces progress when provided) */
  children?: ReactNode;
}

export default function PageSidebar({
  badge,
  title,
  subtitle,
  sections,
  currentSection,
  onSectionChange,
  progress,
  children,
}: PageSidebarProps) {
  return (
    <aside className="h-fit rounded-3xl border border-slate-200 bg-white p-5 shadow-sm xl:sticky xl:top-6">
      <div className="mb-6">
        {badge ? (
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{badge}</div>
        ) : null}
        <h1 className={`text-2xl font-bold ${badge ? "mt-2" : ""}`}>{title}</h1>
        {subtitle ? <p className="mt-2 text-sm text-slate-500">{subtitle}</p> : null}
      </div>

      <div className="space-y-2 text-sm">
        {sections.map((section, index) => {
          const active = currentSection === section.id;
          return (
            <a
              key={section.id}
              href={`#${section.id}`}
              onClick={(e) => {
                e.preventDefault();
                onSectionChange(section.id);
                document.getElementById(section.id)?.scrollIntoView({ behavior: "smooth" });
              }}
              className={`flex items-center gap-3 rounded-xl px-3 py-3 transition ${active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}
            >
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${active ? "bg-white/20 text-white" : "bg-slate-100 text-slate-600"}`}
              >
                {index + 1}
              </span>
              <span>{section.label}</span>
            </a>
          );
        })}
      </div>

      {children != null ? (
        <div className="mt-6">{children}</div>
      ) : progress != null ? (
        <div className="mt-6 rounded-2xl bg-slate-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm font-medium text-slate-800">Progress</div>
            <div className="text-xs font-semibold text-slate-500">{progress.percent}%</div>
          </div>
          <div className="mt-3 h-2 rounded-full bg-slate-200">
            <div
              className="h-2 rounded-full bg-slate-900 transition-all"
              style={{ width: `${Math.min(100, Math.max(0, progress.percent))}%` }}
            />
          </div>
          {progress.label ? <p className="mt-2 text-xs text-slate-500">{progress.label}</p> : null}
        </div>
      ) : null}
    </aside>
  );
}

import { Sidebar } from "./Sidebar";
import { OrgGate } from "./OrgGate";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <OrgGate>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 px-8 py-8 max-w-6xl">{children}</main>
      </div>
    </OrgGate>
  );
}

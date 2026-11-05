import { type LucideIcon } from "lucide-react";

interface PageStubProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function PageStub({ title, description, icon: Icon }: PageStubProps) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-border bg-surface">
        <Icon size={24} className="text-hive" />
      </div>
      <h1 className="mb-2 font-display text-2xl font-semibold">{title}</h1>
      <p className="max-w-sm text-sm text-gray-500">{description}</p>
      <div className="mt-6 rounded-md border border-border bg-surface px-4 py-2 font-mono text-[10px] text-gray-500">
        MILESTONE 2+
      </div>
    </div>
  );
}

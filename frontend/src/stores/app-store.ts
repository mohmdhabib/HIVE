import { create } from "zustand";

interface AppState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  selectedWorkerId: string | null;
  setSelectedWorker: (id: string | null) => void;
  systemOnline: boolean;
  setSystemOnline: (online: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  selectedWorkerId: "tech",
  setSelectedWorker: (id) => set({ selectedWorkerId: id }),
  systemOnline: false,
  setSystemOnline: (online) => set({ systemOnline: online }),
}));

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import OverviewPage from "@/pages/overview";
import MasterAgentPage from "@/pages/master-agent";
import WorkersPage from "@/pages/workers";
import WorkerDetailsPage from "@/pages/worker-details";
import ContentStudioPage from "@/pages/content-studio";
import ApprovalQueuePage from "@/pages/approval-queue";
import PublishingPage from "@/pages/publishing";
import AnalyticsPage from "@/pages/analytics";
import RevenuePage from "@/pages/revenue";
import IntegrationsPage from "@/pages/integrations";
import SystemHealthPage from "@/pages/system-health";
import SettingsPage from "@/pages/settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Shell />}>
            <Route index element={<OverviewPage />} />
            <Route path="master-agent" element={<MasterAgentPage />} />
            <Route path="workers" element={<WorkersPage />} />
            <Route path="workers/:id" element={<WorkerDetailsPage />} />
            <Route path="content-studio" element={<ContentStudioPage />} />
            <Route path="approval-queue" element={<ApprovalQueuePage />} />
            <Route path="publishing" element={<PublishingPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="revenue" element={<RevenuePage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="system" element={<SystemHealthPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type TaskRequest } from "@/lib/api";

export function useWorkers() {
  return useQuery({
    queryKey: ["workers"],
    queryFn: api.workers,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 30_000,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskRequest) => api.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workers"] });
    },
  });
}

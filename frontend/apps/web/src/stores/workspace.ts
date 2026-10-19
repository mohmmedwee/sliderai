import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type WorkspaceState = {
  workspaceId: string | null
  setWorkspace: (id: string | null) => void
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      workspaceId: null,
      setWorkspace: (workspaceId) => set({ workspaceId }),
    }),
    { name: 'docu.workspace' },
  ),
)

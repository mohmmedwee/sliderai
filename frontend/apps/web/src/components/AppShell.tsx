import { Outlet } from 'react-router-dom'

import { NavRail } from '@/components/NavRail'

/** Shell: rail plus the page. T047 restyles this. */
export function AppShell() {
  return (
    <div className="flex h-dvh bg-paper">
      <NavRail />
      <main className="relative min-h-0 min-w-0 flex-1 overflow-auto bg-paper-2 p-6 pb-20 md:pb-6">
        <Outlet />
      </main>
    </div>
  )
}

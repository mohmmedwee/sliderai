import {
  Brain,
  FileText,
  LayoutTemplate,
  MessagesSquare,
  Plug,
  Plus,
  Settings,
  Shield,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { LucideIcon } from 'lucide-react'

import { LanguageToggle } from '@/components/LanguageToggle'

type LinkItem = {
  to: string
  label: string
  Icon: LucideIcon
  match: (path: string) => boolean
}

export function NavRail() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  const mainLinks: LinkItem[] = [
    {
      to: '/documents',
      label: t('nav.documents'),
      Icon: FileText,
      match: (path) => path.startsWith('/documents') || path.startsWith('/doc/'),
    },
    {
      to: '/conversations',
      label: t('nav.conversations'),
      Icon: MessagesSquare,
      match: (path) => path.startsWith('/conversations'),
    },
    {
      to: '/templates',
      label: t('nav.templates'),
      Icon: LayoutTemplate,
      match: (path) => path.startsWith('/templates'),
    },
    {
      to: '/memory',
      label: t('nav.memory'),
      Icon: Brain,
      match: (path) => path.startsWith('/memory'),
    },
    {
      to: '/skills',
      label: t('nav.skills'),
      Icon: Sparkles,
      match: (path) => path.startsWith('/skills'),
    },
    {
      to: '/connectors',
      label: t('nav.connectors'),
      Icon: Plug,
      match: (path) => path.startsWith('/connectors'),
    },
  ]

  const mobileLinks: LinkItem[] = [
    ...mainLinks.slice(0, 4),
    {
      to: '/settings',
      label: t('nav.settings'),
      Icon: Settings,
      match: (path) => path.startsWith('/settings'),
    },
  ]

  return (
    <>
      <nav
        aria-label={t('nav.main')}
        className="hidden h-full w-[68px] shrink-0 flex-col items-center gap-1.5 bg-rail py-4 md:flex"
      >
        <button
          type="button"
          onClick={() => navigate('/')}
          aria-label={t('nav.newChat')}
          title={t('nav.newChat')}
          className="mb-3.5 flex size-11 items-center justify-center rounded-[14px] bg-primary text-white transition hover:bg-primary-600"
        >
          <Plus width={18} height={18} />
        </button>

        {mainLinks.map(({ to, label, Icon, match }) => {
          const active = match(location.pathname)
          return (
            <NavLink
              key={to}
              to={to}
              aria-label={label}
              title={label}
              className={`flex size-11 items-center justify-center rounded-xl transition ${
                active ? 'bg-rail-active text-white' : 'text-rail-icon hover:bg-rail-active/60 hover:text-white'
              }`}
            >
              <Icon width={18} height={18} />
            </NavLink>
          )
        })}

        <div className="flex-1" />
        <LanguageToggle variant="rail" />
        <NavLink
          to="/admin"
          aria-label={t('nav.admin')}
          title={t('nav.admin')}
          className={({ isActive }) =>
            `flex size-11 items-center justify-center rounded-xl transition ${
              isActive ? 'bg-rail-active text-white' : 'text-rail-icon hover:bg-rail-active/60 hover:text-white'
            }`
          }
        >
          <Shield width={18} height={18} />
        </NavLink>
        <NavLink
          to="/trash"
          aria-label={t('nav.trash')}
          title={t('nav.trash')}
          className={({ isActive }) =>
            `flex size-11 items-center justify-center rounded-xl transition ${
              isActive ? 'bg-rail-active text-white' : 'text-rail-icon hover:bg-rail-active/60 hover:text-white'
            }`
          }
        >
          <Trash2 width={18} height={18} />
        </NavLink>
        <NavLink
          to="/settings"
          aria-label={t('nav.settings')}
          title={t('nav.settings')}
          className={({ isActive }) =>
            `flex size-11 items-center justify-center rounded-xl transition ${
              isActive ? 'bg-rail-active text-white' : 'text-rail-icon hover:bg-rail-active/60 hover:text-white'
            }`
          }
        >
          <Settings width={18} height={18} />
        </NavLink>
      </nav>

      <nav
        aria-label={t('nav.main')}
        className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-stretch border-t border-rail-active bg-rail pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {mobileLinks.map(({ to, label, Icon, match }) => {
          const active = match(location.pathname)
          return (
            <NavLink
              key={to}
              to={to}
              className={`flex min-w-[44px] flex-1 flex-col items-center justify-center gap-0.5 text-[10px] transition ${
                active ? 'text-white' : 'text-rail-icon'
              }`}
            >
              <Icon width={18} height={18} />
              <span>{label}</span>
            </NavLink>
          )
        })}
      </nav>
    </>
  )
}

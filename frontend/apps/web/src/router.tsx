import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '@/components/AppShell'

function lazyPage(titleKey: string) {
  return async () => {
    const { Page } = await import('./pages/Page')
    return {
      Component: function TitledPage() {
        return <Page titleKey={titleKey} />
      },
    }
  }
}

export const router = createBrowserRouter([
  { path: '/login', lazy: lazyPage('nav.login') },
  { path: '/register', lazy: lazyPage('nav.register') },
  { path: '/s/:token', lazy: lazyPage('nav.share') },
  {
    path: '/',
    Component: AppShell,
    children: [
      { index: true, lazy: lazyPage('nav.home') },
      { path: 'documents', lazy: lazyPage('nav.documents') },
      { path: 'conversations', lazy: lazyPage('nav.conversations') },
      { path: 'templates', lazy: lazyPage('nav.templates') },
      { path: 'memory', lazy: lazyPage('nav.memory') },
      { path: 'skills', lazy: lazyPage('nav.skills') },
      { path: 'connectors', lazy: lazyPage('nav.connectors') },
      { path: 'settings/*', lazy: lazyPage('nav.settings') },
      { path: 'admin/*', lazy: lazyPage('nav.admin') },
      { path: 'trash', lazy: lazyPage('nav.trash') },
      { path: 'doc/:id', lazy: lazyPage('nav.editor') },
    ],
  },
  { path: '*', lazy: lazyPage('nav.notFound') },
])

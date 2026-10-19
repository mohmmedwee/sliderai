import { useTranslation } from 'react-i18next'

export function Page({ titleKey }: { titleKey: string }) {
  const { t } = useTranslation()
  return <h1>{t(titleKey)}</h1>
}

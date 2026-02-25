import { getRequestConfig } from 'next-intl/server';

export default getRequestConfig(async ({ requestLocale }) => {
  const locale = (await requestLocale) ?? 'fr';

  const landing = (await import(`../messages/${locale}/landing.json`)).default;
  const generator = (await import(`../messages/${locale}/generator.json`)).default;

  return {
    locale,
    messages: { ...landing, generator },
    timeZone: 'Europe/Paris',
  };
});

const LOCALE_SEGMENT = /^[a-z]{2,3}[-_][a-z]{2}$/i;

export function deriveLocaleFromUrl(url: string): string | null {
  try {
    const segments = new URL(url).pathname.split("/").filter(Boolean);
    const localeSegment = segments.find((segment) => LOCALE_SEGMENT.test(segment));
    if (!localeSegment) return null;
    const [language, country] = localeSegment.replace("_", "-").split("-");
    return `${language.toLowerCase()}-${country.toUpperCase()}`;
  } catch {
    return null;
  }
}

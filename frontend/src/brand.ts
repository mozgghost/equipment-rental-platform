const configuredName = import.meta.env.VITE_APP_NAME?.trim();

export const APP_NAME = configuredName || 'Equipment Rental Platform';
export const BRAND_MARK = APP_NAME.trim().slice(0, 1).toLowerCase() || 'e';

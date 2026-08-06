const RADIUS_MONTHS = {
  Jan: '01',
  Feb: '02',
  Mar: '03',
  Apr: '04',
  May: '05',
  Jun: '06',
  Jul: '07',
  Aug: '08',
  Sep: '09',
  Oct: '10',
  Nov: '11',
  Dec: '12',
};

export const toTrimmedString = (value) => {
  const normalized = (value ?? '').toString().trim();
  return normalized || undefined;
};

export const toOptionalNumber = (value) => {
  const normalized = toTrimmedString(value);
  if (normalized === undefined) {
    return undefined;
  }

  const numericValue = Number(normalized);
  return Number.isNaN(numericValue) ? undefined : numericValue;
};

export const formatExpirationForDateInput = (value) => {
  const normalized = toTrimmedString(value);
  if (!normalized) {
    return '';
  }

  const isoMatch = normalized.match(/^(\d{4}-\d{2}-\d{2})/);
  if (isoMatch) {
    return isoMatch[1];
  }

  const radiusMatch = normalized.match(/^(\d{2}) ([A-Za-z]{3}) (\d{4})/);
  if (radiusMatch) {
    const [, day, monthName, year] = radiusMatch;
    const month = RADIUS_MONTHS[monthName];
    if (month) {
      return `${year}-${month}-${day}`;
    }
  }

  const parsedDate = new Date(normalized);
  if (!Number.isNaN(parsedDate.getTime())) {
    const year = parsedDate.getFullYear();
    const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
    const day = String(parsedDate.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  return '';
};

export const buildUserPayload = (formData, { requirePassword = false } = {}) => {
  const password = toTrimmedString(formData.password);

  if (requirePassword && !password) {
    throw new Error('Password is required');
  }

  return {
    username: toTrimmedString(formData.username),
    ...(password ? { password } : {}),
    group_name: toTrimmedString(formData.group_name),
    rate_limit: toTrimmedString(formData.rate_limit),
    session_timeout: toOptionalNumber(formData.session_timeout),
    max_down: toOptionalNumber(formData.max_down),
    max_up: toOptionalNumber(formData.max_up),
    idle_timeout: toOptionalNumber(formData.idle_timeout),
    expiration: formatExpirationForDateInput(formData.expiration) || undefined,
    status: toTrimmedString(formData.status) || 'active',
  };
};

export const buildPackagePayload = (formData) => ({
  groupname: toTrimmedString(formData.groupname),
  rate_limit: toTrimmedString(formData.rate_limit),
  session_timeout: toOptionalNumber(formData.session_timeout),
  max_down: toOptionalNumber(formData.max_down),
  max_up: toOptionalNumber(formData.max_up),
  idle_timeout: toOptionalNumber(formData.idle_timeout),
});

export const buildNasPayload = (formData) => ({
  nasname: toTrimmedString(formData.nasname),
  shortname: toTrimmedString(formData.shortname),
  type: toTrimmedString(formData.type),
  secret: toTrimmedString(formData.secret),
  ports: toOptionalNumber(formData.ports),
  server: toTrimmedString(formData.server),
  community: toTrimmedString(formData.community),
  description: toTrimmedString(formData.description),
});
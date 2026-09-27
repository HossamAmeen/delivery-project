/**
 * English UI strings. Every user-facing string lives here so a second locale (and RTL)
 * can be added once BLK-009 decides the languages. Do not inline UI text in components.
 */
export const en = {
  app: {
    skipToContent: 'Skip to content',
    logoAlt: '{appName} logo',
  },
  common: {
    retry: 'Try again',
    logout: 'Log out',
    loading: 'Loading…',
    goHome: 'Go to start page',
    statusLink: 'Service status',
  },
  login: {
    title: 'Sign in',
    subtitle: 'Sign in to continue.',
    username: 'Username',
    password: 'Password',
    submit: 'Sign in',
    submitting: 'Signing in…',
    usernameRequired: 'Username is required.',
    passwordRequired: 'Password is required.',
    rateLimited: 'Too many sign-in attempts. Please wait and try again.',
    rateLimitedSeconds: 'Too many sign-in attempts. Please try again in {seconds} seconds.',
    sessionExpired: 'Your session has ended. Please sign in again.',
    genericError: 'Sign-in failed. Please try again.',
  },
  status: {
    title: 'Service status',
    apiBaseUrl: 'API address',
    notConfigured: '(not configured)',
    checking: 'Checking the API…',
    reachable: 'API reachable',
    reachableDetail: 'The Flash API answered normally.',
    unexpected: 'API answered with status "{status}".',
    unreachable: 'API unreachable',
    unreachableDetail: 'The Flash API could not be reached. Check your connection and try again.',
    serverError: 'The Flash API returned an error ({httpStatus}).',
    rateLimited: 'Rate-limited',
    rateLimitedDetail: 'Too many status checks. Please wait before trying again.',
    rateLimitedSeconds: 'Too many status checks. Please try again in {seconds} seconds.',
    sessionTitle: 'Signed-in user',
    notSignedIn: 'Not signed in',
    notSignedInDetail: 'Sign in to see your account here.',
    signIn: 'Sign in',
    username: 'Username',
    role: 'Role',
    sessionError: 'Could not load your account.',
  },
  areas: {
    customer: 'Customer area',
    driver: 'Driver area',
    store: 'Store area',
    admin: 'Admin area',
    placeholder: 'This area is being prepared. Screens will appear here in upcoming releases.',
    signedInAs: 'Signed in as {username}',
  },
  roles: {
    CUSTOMER: 'Customer',
    DRIVER: 'Driver',
    STORE: 'Store',
    ADMIN: 'Admin',
  },
  notFound: {
    title: 'Page not found',
    detail: 'The page you are looking for does not exist.',
  },
  errors: {
    network: 'Cannot reach the server. Check your connection and try again.',
    forbidden: 'You do not have access to this.',
    notFound: 'Not found.',
    server: 'Something went wrong on the server. Please try again later.',
    rateLimited: 'Too many requests. Please wait and try again.',
    generic: 'Something went wrong. Please try again.',
  },
} as const

export type Messages = typeof en

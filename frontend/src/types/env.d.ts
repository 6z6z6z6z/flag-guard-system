declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test'
    VUE_APP_TITLE: string
    VUE_APP_API_BASE_URL: string
    VUE_APP_UPLOAD_URL: string
  }
} 
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://app:8000/api/v1/:path*',
      },
      {
        source: '/backend/:path*',
        destination: 'http://app:8000/:path*',
      },
    ]
  },
}

module.exports = nextConfig
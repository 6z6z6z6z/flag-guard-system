const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')
const path = require('path')

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
    plugins: [
      new webpack.DefinePlugin({
        __VUE_OPTIONS_API__: JSON.stringify(true),
        __VUE_PROD_DEVTOOLS__: JSON.stringify(false),
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false),
        __VUE_PROD_HYDRATION_MISMATCH_LOGGING__: JSON.stringify(false),
        __VUE_PROD_TIPS__: JSON.stringify(false),
        __VUE_PROD_WARNINGS__: JSON.stringify(false),
        __VUE_PROD_HYDRATION__: JSON.stringify(true)
      })
    ],
    optimization: {
      splitChunks: {
        chunks: 'all',
        minSize: 20000,
        maxSize: 244000,
        cacheGroups: {
          vendors: {
            name: 'chunk-vendors',
            test: /[\\/]node_modules[\\/]/,
            priority: -10,
            chunks: 'initial'
          },
          common: {
            name: 'chunk-common',
            minChunks: 2,
            priority: -20,
            chunks: 'initial',
            reuseExistingChunk: true
          }
        }
      }
    }
  },
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        ws: true,
        onProxyReq: function(proxyReq, req, res) {
          console.log('Proxying request:', req.method, req.url)
        },
        onProxyRes: function(proxyRes, req, res) {
          console.log('Received response:', proxyRes.statusCode, req.url)
        },
        onError: function(err, req, res) {
          console.error('Proxy error:', err)
        }
      },
      '/uploads': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: { '^/uploads': '/api/files/uploads' },
        secure: false
      }
    },
    client: {
      overlay: {
        runtimeErrors: (error) => {
          if (error.message.includes('ResizeObserver loop')) {
            return false
          }
          return true
        }
      }
    },
    hot: true,
    compress: true,
    historyApiFallback: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization'
    }
  },
  chainWebpack: config => {
    config.plugin('html').tap(args => {
      args[0].title = '国旗护卫队管理系统'
      return args
    })
    
    config.module
      .rule('images')
      .use('url-loader')
      .loader('url-loader')
      .tap(options => Object.assign(options || {}, { limit: 10240 }))
      
    config.plugin('copy').tap(args => {
      const options = args[0] || { patterns: [] }
      
      if (!options.patterns) {
        options.patterns = []
      }
      
      options.patterns.push({
        from: 'public/favicon.ico',
        to: 'favicon.ico',
        noErrorOnMissing: true
      })
      
      args[0] = options
      return args
    })
  }
})

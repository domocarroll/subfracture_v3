# SUBFRACTURE Brand Intelligence Platform

Real-time brand intelligence and 3D visualization system with WebSocket integration and liquid glass aesthetics.

## 🚀 Features

- **Real-Time Dashboard**: Monitor brand intelligence metrics live
- **3D Liquid Glass Visualization**: Advanced Three.js rendering with WebGL
- **Workshop Simulation**: Test real-time data flow and updates
- **API Integration**: RESTful endpoints for brand data management
- **Cloud-Native**: Optimized for serverless deployment on Vercel

## 🌐 Live Demo

- **Main Dashboard**: `/` - Central hub with status indicators
- **Real-Time Demo**: `/demo` - Live 3D brand visualization
- **Original Demo**: `/demo-liquid-glass.html` - Static version

## 🔧 API Endpoints

- `GET /api/websocket-server/brand/:brandId/state` - Get brand state
- `POST /api/websocket-server/workshop/process` - Process workshop data
- `POST /api/websocket-server/ai/cognitive-state` - Update AI state
- `POST /api/websocket-server/refinement/dialogue` - Add dialogue

## 🏗️ Architecture

### Frontend
- **HTML5/CSS3/JavaScript**: Modern web standards
- **Three.js**: 3D graphics and WebGL rendering
- **WebSocket/HTTP Polling**: Real-time communication
- **Responsive Design**: Mobile and desktop compatible

### Backend (Serverless)
- **Vercel Functions**: Node.js serverless API
- **Express.js**: Lightweight request handling
- **Client-Side Storage**: localStorage for state persistence
- **CORS Enabled**: Cross-origin resource sharing

## 📦 Deployment

### Vercel (Recommended)
```bash
# Deploy with Vercel CLI
vercel --prod

# Or connect GitHub repository to Vercel dashboard
```

### Local Development
```bash
# Install dependencies
npm install

# Start local server
npm start

# Start with auto-reload
npm run dev
```

## 🔧 Configuration

### Environment Variables
- `NODE_ENV`: Set to "production" for cloud deployment
- Custom variables can be added to `vercel.json`

### Build Settings
- **Build Command**: `npm run build` (static files)
- **Output Directory**: Root directory (static files)
- **Install Command**: `npm install`

## 🎨 Customization

### Brand Data
Edit brand dimensions in API responses:
```javascript
const brandDimensions = [
  { name: 'market_position', signalStrength: 0.5, coherence: 0.7 },
  // Add more dimensions...
];
```

### Visual Themes
Modify CSS variables in HTML files for custom branding.

## 🔒 Security

- CORS headers configured for cross-origin requests
- X-Frame-Options set to DENY (prevents clickjacking)
- Content-Type sniffing disabled
- Client-side state management (no server secrets)

## 📊 Performance

- **Optimized Three.js**: Efficient 3D rendering
- **Compression**: Gzip enabled on Vercel
- **CDN**: Global edge network for fast delivery
- **Hybrid Architecture**: Local state + cloud validation

## 🐛 Troubleshooting

### Common Issues

1. **API 401/404 Errors**: Check Vercel function deployment
2. **Three.js Not Loading**: Verify CDN availability and fallbacks
3. **Connection Issues**: System falls back to offline mode
4. **CORS Errors**: Ensure headers are properly configured

### Debug Mode
Add `?debug=true` to any URL to enable debug logging.

---

**Built for the future of brand intelligence**
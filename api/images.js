const fs = require('fs');
const path = require('path');

let cachedImages = null;

function loadImages() {
  if (cachedImages) return cachedImages;
  const filePath = path.join(process.cwd(), 'public', 'imagesupdates_android_compressed.json');
  if (fs.existsSync(filePath)) {
    const raw = fs.readFileSync(filePath, 'utf-8');
    const parsed = JSON.parse(raw);
    cachedImages = parsed.images || [];
  } else {
    cachedImages = [];
  }
  return cachedImages;
}

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');

  const { page = '1', limit = '30', tag, free } = req.query;
  const p = Math.max(1, parseInt(page, 10) || 1);
  const l = Math.max(1, Math.min(100, parseInt(limit, 10) || 30));

  let images = loadImages();

  if (tag) {
    const searchTag = tag.toLowerCase().trim();
    images = images.filter(img => img.tags && img.tags.some(t => t.toLowerCase().trim() === searchTag));
  }

  if (free !== undefined) {
    const isFree = free === 'true';
    images = images.filter(img => (img.free === true || img.free === 'true') === isFree);
  }

  const total = images.length;
  const totalPages = Math.ceil(total / l);
  const start = (p - 1) * l;
  const end = start + l;
  const items = images.slice(start, end).map(img => {
    const isGif = img.gif === true || img.contentType === 'gif';
    const ext = isGif ? '.gif' : '.png';
    return {
      id: img.id,
      url: `https://npngocanh228.github.io/Color-DB/public/images/${img.id}${ext}`,
      free: img.free === true || img.free === 'true',
      gif: isGif,
      pixelCount: img.pixelCount || 0,
      release_date: img.release_date || '',
      tags: img.tags || []
    };
  });

  return res.status(200).json({
    page: p,
    limit: l,
    total_items: total,
    total_pages: totalPages,
    has_more: p < totalPages,
    images: items
  });
};

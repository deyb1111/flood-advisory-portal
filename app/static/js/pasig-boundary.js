(function () {
  'use strict';
  window.PasigBoundary = {
    async init(map, url) {
      const geo = await (await fetch(url)).json();
      const boundary = L.geoJSON(geo, {
        style: { color: '#0d6efd', weight: 2, fillOpacity: 0 }, interactive: false
      }).addTo(map);

      // Grey out everything outside Pasig (Pasig rings become holes in a world polygon)
      const world = [[-90, -180], [-90, 180], [90, 180], [90, -180]];
      const holes = [];
      geo.features.forEach(f => {
        const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
        polys.forEach(p => holes.push(L.GeoJSON.coordsToLatLngs(p[0], 0)));
      });
      L.polygon([world, ...holes], {
        stroke: false, fillColor: '#000', fillOpacity: 0.4, interactive: false
      }).addTo(map);

      // Lock the view to Pasig
      const bounds = boundary.getBounds();
      const padded = bounds.pad(0.1);
      map.options.maxBoundsViscosity = 1.0;
      map.setMaxBounds(padded);
      map.fitBounds(bounds);
      map.setMinZoom(map.getBoundsZoom(padded));

      return {
        bounds,
        isInside: (lat, lng) =>
          geo.features.some(f => turf.booleanPointInPolygon(turf.point([lng, lat]), f))
      };
    }
  };
})();
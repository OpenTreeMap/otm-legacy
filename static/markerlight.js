/* A Bar is a simple overlay that outlines a lat/lng bounds on the
 * map. It has a border of the given weight and color and can optionally
 * have a semi-transparent background color.
 * @param latlng {GLatLng} Point to place bar at.
 * @param opts {Object Literal} Passes configuration options - 
 *   weight, color, height, width, text, and offset.
 */
function MarkerLight(latlng, opts) {
  this.latlng = latlng;

  if (!opts) opts = {};

  this.height_ = opts.height || 32;
  this.width_ = opts.width || 32;
  this.image_ = opts.image;
  this.imageOver_ = opts.imageOver;
  this.clicked_ = 0;
}

/* MarkerLight extends GOverlay class from the Google Maps API
 */
MarkerLight.prototype = new GOverlay();

/* Creates the DIV representing this MarkerLight.
 * @param map {GMap2} Map that bar overlay is added to.
 */
MarkerLight.prototype.initialize = function(map) {
  var me = this;

  // Create the DIV representing our MarkerLight
  var div = document.createElement("div");
  div.style.border = "0px solid white";
  div.style.position = "absolute";
  div.style.paddingLeft = "0px";
  div.style.cursor = 'pointer';

  var img = document.createElement("img");
  img.src = me.image_;
  img.style.width = me.width_ + "px";
  img.style.height = me.height_ + "px";
  div.appendChild(img);  

  GEvent.addDomListener(div, "click", function(event) {
    me.clicked_ = 1;
    GEvent.trigger(me, "click");
  });

  map.getPane(G_MAP_MARKER_PANE).appendChild(div);

  this.map_ = map;
  this.div_ = div;
};

/* Remove the main DIV from the map pane
 */
MarkerLight.prototype.remove = function() {
  this.div_.parentNode.removeChild(this.div_);
};

/* Copy our data to a new MarkerLight
 * @return {MarkerLight} Copy of bar
 */
MarkerLight.prototype.copy = function() {
  var opts = {};
  opts.color = this.color_;
  opts.height = this.height_;
  opts.width = this.width_;
  opts.image = this.image_;
  opts.imageOver = this.image_;
  return new MarkerLight(this.latlng, opts);
};

/* Redraw the MarkerLight based on the current projection and zoom level
 * @param force {boolean} Helps decide whether to redraw overlay
 */
MarkerLight.prototype.redraw = function(force) {

  // We only need to redraw if the coordinate system has changed
  if (!force) return;

  // Calculate the DIV coordinates of two opposite corners 
  // of our bounds to get the size and position of our MarkerLight
  var divPixel = this.map_.fromLatLngToDivPixel(this.latlng);

  // Now position our DIV based on the DIV coordinates of our bounds
  this.div_.style.width = this.width_ + "px";
  this.div_.style.left = (divPixel.x) - (this.width_ / 2) + "px"
  this.div_.style.height = (this.height_) + "px";
  this.div_.style.top = (divPixel.y) - (this.height_ / 2) + "px";
};

MarkerLight.prototype.getZIndex = function(m) {
  return GOverlay.getZIndex(marker.getPoint().lat())-m.clicked*10000;
}

MarkerLight.prototype.getPoint = function() {
  return this.latlng;
};

MarkerLight.prototype.setStyle = function(style) {
  for (s in style) {
    this.div_.style[s] = style[s];
  }
};

MarkerLight.prototype.setImage = function(image) {
  this.div_.style.background = 'url("' + image + '")';
}


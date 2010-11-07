/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * @name Tabbed Max Content
 * @version 1.0
 * @author: Nianwei Liu [nianwei at gmail dot com]
 * @fileoverview This library provides a max info window UI that's similar 
 *  to the info window UI for local business results on Google Maps. It lets a 
 *  developer pass in an array of content that will be rendered in tabs in the 
 *  maximized state of an info window.
 */
(function () {
  /*jslint browser:true */
  /*global GMap2,GMarker,GEvent */
  var defaultStyle = {
    tabBar: {
      background: '#F4F4F4 none repeat scroll 0 0',
      borderBottom: '1px solid #B0B0B0',
      padding: '6px 8px 4px',
      marginRight: '13px',
      whiteSpace: 'nowrap',
      verticalAlign: 'bottom'
    },
    tabLeft: {},
    tabRight: {},
    tabOn: {
      background: '#FFFFFF none repeat scroll 0 0',
      padding: '6px 8px 4px',
      borderTop: '1px solid #B0B0B0',
      borderLeft:  '1px solid #B0B0B0',
      borderRight:  '1px solid #B0B0B0',
      borderBottom: '2px solid #FFFFFF',
      color: '#000000',
      textDecoration: 'none',
      fontWeight: 'bold'
    },
    tabOff: {
      background: '#F4F4F4 none repeat scroll 0 0',
      padding: '6px 8px 4px',
      color: '#0000FF',
      border: 'none',
      textDecoration: 'underline',
      fontWeight: 'normal'
    },
    content: {
      borderStyle: 'none solid solid solid',
      borderWidth: '1px',
      borderColor: '#B0B0B0',
      borderTop: 'none',
      overflow: 'auto'
    },
    summary: {
      overflow: 'auto',
      marginBottom: '5px'
    }
  };
  /**
   * set the property of object from another object
   * @param {Object} obj target object
   * @param {Object} vals source object
   */
  var setVals = function (obj, vals) {
    if (obj && vals) {
      for (var x in vals) {
        if (vals.hasOwnProperty(x)) {
          if (obj[x] && typeof vals[x] === 'object') {
            obj[x] = setVals(obj[x], vals[x]);
          } else {
            obj[x] = vals[x];
          }
        }
      }
    }
    return obj;
  };
  /**
   * Create an element
   * @param {String} tag of element
   * @param {Object} attrs name-value of attributes as json
   * @param {String|Node} content DOM node or HTML
   * @param {Object} style css object to set to the element
   * @param {Node} parent if supplied, the node will be appended to the parent
   * @return {Node} the new or modified node
   */
  var createEl = function (tag, attrs, content, style, parent) {
    var node = content;
    if (!content || (content && typeof content === 'string')) {
      node = document.createElement(tag);
      node.innerHTML = content || ''; 
    }
    if (style) {
      setVals(node.style, style);
    }
    if (attrs) {
      setVals(node, attrs);
    }
    if (parent) {
      parent.appendChild(node);
    }
    return node;
  };
  
  /**
   * Get the offset position up to given parent
   * @param {Node} el
   * @param {Node} parent if null will get the DOM root.
   */
  var getPosition = function (el, parent) {
    var leftPos = 0;
    var topPos = 0;
    var par = el;
    while (par && par !== parent) {
      leftPos += par.offsetLeft;
      topPos += par.offsetTop;
      par = par.offsetParent;
    }
    return {
      left: leftPos,
      top: topPos
    };
  };
  
  /**
   * Creates a content tab data structure that can be passed in the <code>tabs</code> argument
   * in the <code>openMaxContentTabs*()</code> methods.
   * @name MaxContentTab
   * @class This class represents a tab in the maximized info window. An array of
   *  instances of this class can be passed in as the {@link tabs} argument to 
   *  the methods <code>openMaxContentTabs*()</code> etc.
   * This class is similar to the 
   * <a target=_blank href=http://code.google.com/apis/maps/documentation/reference.html#GInfoWindowTab>GInfoWindowTab</a>
   * class in the core API.
   * @param {String} label
   * @param {Node|String} content 
   */
  function MaxContentTab(label, content) {
    this.label_ = label;
    this.contentNode_ = createEl('div', null, content, null, null);
    this.navNode_ = null;
  }

   /**
   * Returns the label of the tab.
   * @return {String} label
   */
  MaxContentTab.prototype.getLabel = function () {
    return this.label_;
  };

  /**
   * Returns the content of the tab.
   * @return {Node} conent
   */
  MaxContentTab.prototype.getContentNode = function () {
    return this.contentNode_;
  };
  
 /**
 * @name TabbedMaxContent
 * @class This class represent the max content in the info window. 
 * There is no public constructor for this class. If needed, it can be accessed 
 * via  <code>GMap2.getTabbedMaxContent()</code>.
 * @param {GInfoWindow} iw 
 */
  function TabbedMaxContent(iw) {
    this.infoWindow_ = iw;
    GEvent.bind(iw, 'maximizeclick', this, this.onMaximizeClick_);
    GEvent.bind(iw, 'restoreclick', this, this.onRestoreClick_);
    GEvent.bind(iw, 'maximizeend', this, this.onMaximizeEnd_);
    this.style_ = {};
    this.maxNode_ = null;
    this.summaryNode_ = null;
    this.navsNode_ = null;
    this.contentsNode_ = null;
    this.tabs_ = [];
  }
  
  /**
   * Before open infowindow, setup contents
   * @param {Node} sumNode summary node
   * @param {GInfoWindowTabs[]} tabs
   * @param {MaxInfoWindowOptions} opt_maxOptions
   * @private
   */
  TabbedMaxContent.prototype.initialize_ = function (sumNode, tabs, opt_maxOptions) {
    this.tabs_ = tabs;
    this.selectedTab_ = -1;
    if (this.maxNode_) {
      GEvent.clearNode(this.maxNode_);
      this.maxNode_ = null;
    } 
    this.maxNode_ = createEl('div', {
        id: 'maxcontent'
    });
    opt_maxOptions = opt_maxOptions || {};
    var selectedTab = opt_maxOptions.selectedTab || 0;
    this.style_ = setVals({}, defaultStyle);
    this.style_ = setVals(this.style_, opt_maxOptions.style);
    this.summaryNode_ = createEl('div', null, sumNode, this.style_.summary, this.maxNode_);
    this.navsNode_ = createEl('div', null, null, this.style_.tabBar, this.maxNode_);
    this.contentsNode_ = createEl('div', null, null, null, this.maxNode_);
    if (tabs && tabs.length) {
      // left
      createEl('span', null, null, this.style_.tabLeft, this.navsNode_);
      for (var i = 0, ct = tabs.length; i < ct; i++) {
        if (i === selectedTab || tabs[i].getLabel() === selectedTab) {
          this.selectedTab_ = i;
        }
        tabs[i].navNode_ = createEl('span', null, tabs[i].getLabel(), this.style_.tabOff, this.navsNode_);//);
        var node = createEl('div', null, tabs[i].getContentNode(), this.style_.content, this.contentsNode_);
        node.style.display = 'none';
      }
      // right
      createEl('span', null, null, this.style_.tabRight, this.navsNode_);
    }
  };
  /**
   * Setup event listeners. The core API seems removed all liteners when restored to normal size
   * @private
   */
  TabbedMaxContent.prototype.onMaximizeClick_ = function () {
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      GEvent.addDomListener(this.tabs_[i].navNode_, 'click', GEvent.callback(this, this.selectTab, i));
    }
  };
  
  /**
   * Clean up listeners on tabs.
   * @private
   */
  TabbedMaxContent.prototype.onRestoreClick_ = function () {
    if (this.maxNode_) {
      GEvent.clearNode(this.maxNode_);
    }
  };
  /**
   * Clean up listeners on tabs.
   * @private
   */
  TabbedMaxContent.prototype.onMaximizeEnd_ = function () {
    this.checkResize();
    this.selectTab(this.selectedTab_);
  };
  /**
   * Select a tab using the given index or label.
   * @param {Number|String} identifier
   */
  TabbedMaxContent.prototype.selectTab = function (identifier) {
    var trigger = false;
    var hasVisibleTab = false;
    var tab;
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      tab = this.tabs_[i];
      if (i === identifier || tab.getLabel() === identifier) {
        if (tab.getContentNode().style.display === 'none') {
          setVals(tab.navNode_.style, this.style_.tabOn);
          tab.getContentNode().style.display = 'block';
          this.selectedTab_ = i;  
          trigger = true;
        }
        hasVisibleTab = true; 
      } else {
        setVals(tab.navNode_.style, this.style_.tabOff);
        tab.getContentNode().style.display = 'none';
      }
    }
    // avoid excessive event if clicked on a selected tab.
    if (trigger) {
      /**
       * This event is fired after a tab is selected,
       * passing the selected {@link MaxContentTab} into the callback.
       * @name TabbedMaxContent#selecttab
       * @param {MaxContentTab} selected tab
       * @event
       */
      GEvent.trigger(this, 'selecttab', this.tabs_[this.selectedTab_]);
    }
    if (!hasVisibleTab) {
      this.selectTab(0);
    }
  };
  /**
   * Return the {@link MaxContentTab} at the given index or label.
   * @param {Number|String} identifier
   * @return {MaxContentTab}
   */
  TabbedMaxContent.prototype.getTab = function (identifier) {
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      if (i === identifier || this.tabs_[i].getLabel() === identifier) {
        return this.tabs_[i];
      }
    }
  };
  
  /**
   * Adjust sizes of tabs to fit inside the maximized info window. 
   * This method is automatically called on <code>
   * GInfoWindow</code>'s <code>'maximizeend'</code> event. However, there may
   * be cases where additional content is loaded in after that event,
   * and an additional resize is needed.
   */
  TabbedMaxContent.prototype.checkResize = function () {
    var container = this.infoWindow_.getContentContainers()[0];
    var contents = this.contentsNode_;
    var pos = getPosition(contents, container);
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      var t = this.tabs_[i].getContentNode();
      t.style.width = container.style.width;
      t.style.height = (parseInt(container.style.height, 10) - pos.top) + 'px';
    }
  };


  /**
   * @name MaxContentOptions
   * @class 
   * This class extends <a href='http://code.google.com/apis/maps/documentation/reference.ht    ml#GInfoWindowOptions'><code>GInfoWindowOptions</code></a>. 
   * Instances of this class are used in the <code>opts_maxOption</code> 
   * argument to methods openMaxContentTabs(), openMaxContentTabsHtml(). 
   * Note, <code>GInfoWindowOptions.maxContent</code> can not be specified. 
   * @property {Object} [style] The object that holds a set of css styles 
   * for the maximized content. It has the following properties:
   *     <code> tabOn, tabOff, tabBar, tabLeft, tabRight, content </code>. 
   *  Each property is a css object such as 
   *     <code> {backgroundColor: 'gray', opacity: 0.2}</code>. 
   * @property {Number|String} [selectedTab = 0] Selects the tab with the given 
   * index or name by default when the info window is first maximized.
   * @property {String|Node} [maxTitle = ""] Specifies the title to be shown when
   * the infowindow is maximized.  
   * @property {Boolean} [maximized = false] Specifies if the window should be 
   * opened in the maximized state by default.  
   */
 
  /**
   * @name GMap2
   * @class These are new methods added to the Google Maps API's
   * <a href  = 'http://code.google.com/apis/maps/documentation/reference.html#GMap2'>GMap2</a>
   * class.
   */
  /**
   * Opens an info window with maximizable content at the given {@link latlng}.
   * The infowindow displays the content in the {@link minNode} in the 
   * minimized state, and then displays the content in the {@link summaryNode}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GLatLng} latlng
   * @param {Node} minNode
   * @param {Node} summaryNode
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMap2.prototype.openMaxContentTabs = function (latlng, minNode, sumNode, tabs, opt_maxOptions) {
    var max = this.getTabbedMaxContent();
    var opts = opt_maxOptions || {};
    max.initialize_(sumNode, tabs, opts);
    opts.maxContent = max.maxNode_;
    if (opts.style) {
      delete opts.style;
    }
    if (opts.selectedTab) {
      delete opts.selectedTab;
    }
    if (minNode.style) {
      minNode.style.marginTop = '6px';
    }
    this.openInfoWindow(latlng, minNode, opts);
    if (opts.maximized) {
      var iw = this.getInfoWindow();
      var m = GEvent.addListener(this, 'infowindowopen', function () {
        GEvent.removeListener(m);
        iw.maximize();
      });
    }
  };

  /**
   * Opens an info window with maximizable content at the given {@link latlng}.
   * The infowindow displays the content in the {@link minHtml} in the 
   * minimized state, and then displays the content in the {@link summaryHtml}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GLatLng} latlng
   * @param {String} minHtml
   * @param {String} summaryHtml
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMap2.prototype.openMaxContentTabsHtml = function (latlng, html, summary, tabs, opt_maxOptions) {
    this.openMaxContentTabs(latlng, createEl('div', null, html), createEl('div', null, summary), tabs, opt_maxOptions);
  };

  /**
   * Returns the {@link TabbedMaxContent} for currently opened info window.
   * @return {TabbedMaxContent}
   */
  GMap2.prototype.getTabbedMaxContent = function () {
    this.maxContent_  = this.maxContent_ || new TabbedMaxContent(this.getInfoWindow());
    return this.maxContent_;
  };
  
  /**
   * @name GMarker
   * @class These are new methods added to Google Maps API's
   * <a href  = 'http://code.google.com/apis/maps/documentation/reference.html#GMarker'>GMarker</a>
   * class.
   */

  /**
   * Opens an info window with maximizable content above the marker.
   * The infowindow displays the content in the {@link minHtml} in the 
   * minimized state, and then displays the content in the {@link summaryHtml}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GMap2} map
   * @param {String} minHtml
   * @param {String} summaryHtml
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMarker.prototype.openMaxContentTabsHtml = function (map, minHtml, summaryHtml, tabs, opt_maxOptions) {
    map.openMaxContentTabsHtml(this.getLatLng(), minHtml, summaryHtml, tabs, opt_maxOptions);
  };

  /**
   * Opens an info window with maximizable content above the marker.
   * The infowindow displays the content in the {@link minNode} in the 
   * minimized state, and then displays the content in the {@link summaryNode}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GMap2} map
   * @param {Node} minNode
   * @param {Node} summaryNode
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMarker.prototype.openMaxContentTabs = function (map, minNode, summaryNode, tabs, opt_maxOptions) {
    map.openMaxContentTabs(this.getLatLng(), minNode, summaryNode, tabs, opt_maxOptions);
  };
  
  window.MaxContentTab = MaxContentTab;
})();

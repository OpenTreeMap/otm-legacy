<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>Treemap Tree Points</Name>
    <UserStyle>
      <Title>Treemap Tree Points</Title>
      <Abstract>Styling for PhillyTreeMaps trees layer</Abstract>

      <FeatureTypeStyle>
        <Rule>
          <Name>Zoom1</Name>
          <MaxScaleDenominator>5000</MaxScaleDenominator>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource
                  xlink:type="simple"
                  xlink:href="/home/azavea/UrbanForestMap/mapserver/images/Philadelphia/zoom7b.png" />
                <Format>image/png</Format>
              </ExternalGraphic>
              <Opacity>.7</Opacity>
              <Size>19</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>Zoom3</Name>
          <MinScaleDenominator>5000</MinScaleDenominator>
          <MaxScaleDenominator>10000</MaxScaleDenominator>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource
                  xlink:type="simple"
                  xlink:href="/home/azavea/UrbanForestMap/mapserver/images/Philadelphia/zoom7.png" />
                <Format>image/png</Format>
              </ExternalGraphic>
              <Opacity>.6</Opacity>
              <Size>17</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>Zoom4</Name>
          <MinScaleDenominator>10000</MinScaleDenominator>
          <MaxScaleDenominator>80000</MaxScaleDenominator>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource
                  xlink:type="simple"
                  xlink:href="/home/azavea/UrbanForestMap/mapserver/images/Philadelphia/zoom5.png" />
                <Format>image/png</Format>
              </ExternalGraphic>
              <Opacity>.6</Opacity>
              <Size>8</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>Zoom5</Name>
          <MinScaleDenominator>80000</MinScaleDenominator>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource
                  xlink:type="simple"
                  xlink:href="/home/azavea/UrbanForestMap/mapserver/images/Philadelphia/zoom5.png" />
                <Format>image/png</Format>
              </ExternalGraphic>
              <Opacity>.6</Opacity>
              <Size>4</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>

    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>


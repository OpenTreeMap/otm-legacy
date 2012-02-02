<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>Treemap Tree Points</Name>
    <UserStyle>
      <Title>Treemap Tree Points</Title>
      <Abstract>Styling for PhillyTreeMap's trees layer</Abstract>

      <FeatureTypeStyle>
        <Rule>
          <Name>Zoom1</Name>
          <MaxScaleDenominator>10000</MaxScaleDenominator>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource
                  xlink:type="simple"
                  xlink:href="/home/azavea/UrbanForestMap/mapserver/images/Philadelphia/zoom7.png" />
                <Format>image/png</Format>
              </ExternalGraphic>
              <Size>19</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>Zoom2</Name>
          <MinScaleDenominator>10000</MinScaleDenominator>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource
                  xlink:type="simple"
                  xlink:href="/home/azavea/UrbanForestMap/mapserver/images/Philadelphia/zoom7.png" />
                <Format>image/png</Format>
              </ExternalGraphic>
              <Size>12</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>

    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>


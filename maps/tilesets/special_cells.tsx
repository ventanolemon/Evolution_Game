<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.10.2" name="special_cells" tilewidth="64" tileheight="64" tilecount="4" columns="0">
 <grid orientation="orthogonal" width="1" height="1"/>
 <!-- Tile 0: стена (непроходимая, разрывает линии сдвига) -->
 <tile id="0">
  <properties>
   <property name="type" value="wall"/>
  </properties>
  <image width="64" height="64" source="../../assets/cells/wall.png"/>
 </tile>
 <!-- Tile 1: огонь — уничтожает плитку, остановившуюся на нём -->
 <tile id="1">
  <properties>
   <property name="type" value="fire"/>
  </properties>
  <image width="64" height="64" source="../../assets/cells/fire.png"/>
 </tile>
 <!-- Tile 2: апгрейдер — +1 стадия эволюции -->
 <tile id="2">
  <properties>
   <property name="type" value="upgrade"/>
  </properties>
  <image width="64" height="64" source="../../assets/cells/upgrade.png"/>
 </tile>
 <!-- Tile 3: деградатор — -1 стадия эволюции, уничтожается на стадии 0 -->
 <tile id="3">
  <properties>
   <property name="type" value="degrade"/>
  </properties>
  <image width="64" height="64" source="../../assets/cells/degrade.png"/>
 </tile>
</tileset>

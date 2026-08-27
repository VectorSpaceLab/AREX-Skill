// Agriculture_KnowledgeGraph Neo4j import templates.
// Adapt file names as needed, but keep file:/// URLs relative to Neo4j's import
// directory. Do not replace them with machine-local absolute paths.
//
// These statements use Neo4j 3.x-style constraints because the original project
// targets an old py2neo/Neo4j stack. For Neo4j 4+/5, replace constraints with:
// CREATE CONSTRAINT hudong_title IF NOT EXISTS FOR (c:HudongItem) REQUIRE c.title IS UNIQUE;
// CREATE CONSTRAINT newnode_title IF NOT EXISTS FOR (c:NewNode) REQUIRE c.title IS UNIQUE;
// CREATE CONSTRAINT weather_title IF NOT EXISTS FOR (c:Weather) REQUIRE c.title IS UNIQUE;

// -----------------------------------------------------------------------------
// 0. Optional constraints / indexes
// -----------------------------------------------------------------------------
CREATE CONSTRAINT ON (c:HudongItem) ASSERT c.title IS UNIQUE;
CREATE CONSTRAINT ON (c:NewNode) ASSERT c.title IS UNIQUE;
CREATE CONSTRAINT ON (c:Weather) ASSERT c.title IS UNIQUE;

// -----------------------------------------------------------------------------
// 1. Hudong encyclopedia nodes
// -----------------------------------------------------------------------------
USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///hudong_pedia.csv" AS line
WITH line WHERE line.title IS NOT NULL AND trim(line.title) <> ""
MERGE (p:HudongItem {title: line.title})
SET p.image = line.image,
    p.detail = line.detail,
    p.url = line.url,
    p.openTypeList = line.openTypeList,
    p.baseInfoKeyList = line.baseInfoKeyList,
    p.baseInfoValueList = line.baseInfoValueList;

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///hudong_pedia2.csv" AS line
WITH line WHERE line.title IS NOT NULL AND trim(line.title) <> ""
MERGE (p:HudongItem {title: line.title})
SET p.image = line.image,
    p.detail = line.detail,
    p.url = line.url,
    p.openTypeList = line.openTypeList,
    p.baseInfoKeyList = line.baseInfoKeyList,
    p.baseInfoValueList = line.baseInfoValueList;

// -----------------------------------------------------------------------------
// 2. Wikidata-only nodes
// -----------------------------------------------------------------------------
USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///new_node.csv" AS line
WITH line WHERE line.title IS NOT NULL AND trim(line.title) <> ""
MERGE (:NewNode {title: line.title});

// -----------------------------------------------------------------------------
// 3. Wikidata relations
// -----------------------------------------------------------------------------
USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///wikidata_relation2.csv" AS line
WITH line
WHERE line.HudongItem IS NOT NULL AND line.NewNode IS NOT NULL
  AND trim(line.HudongItem) <> "" AND trim(line.NewNode) <> ""
MATCH (entity1:HudongItem {title: line.HudongItem})
MATCH (entity2:NewNode {title: line.NewNode})
MERGE (entity1)-[rel:RELATION {type: line.relation}]->(entity2);

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///wikidata_relation.csv" AS line
WITH line
WHERE line.HudongItem1 IS NOT NULL AND line.HudongItem2 IS NOT NULL
  AND trim(line.HudongItem1) <> "" AND trim(line.HudongItem2) <> ""
MATCH (entity1:HudongItem {title: line.HudongItem1})
MATCH (entity2:HudongItem {title: line.HudongItem2})
MERGE (entity1)-[rel:RELATION {type: line.relation}]->(entity2);

// -----------------------------------------------------------------------------
// 4. Hudong/Wikidata attribute-derived relations
// -----------------------------------------------------------------------------
USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///attributes.csv" AS line
WITH line WHERE line.Entity IS NOT NULL AND line.Attribute IS NOT NULL
MATCH (entity1:HudongItem {title: line.Entity})
MATCH (entity2:HudongItem {title: line.Attribute})
MERGE (entity1)-[rel:RELATION {type: line.AttributeName}]->(entity2);

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///attributes.csv" AS line
WITH line WHERE line.Entity IS NOT NULL AND line.Attribute IS NOT NULL
MATCH (entity1:HudongItem {title: line.Entity})
MATCH (entity2:NewNode {title: line.Attribute})
MERGE (entity1)-[rel:RELATION {type: line.AttributeName}]->(entity2);

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///attributes.csv" AS line
WITH line WHERE line.Entity IS NOT NULL AND line.Attribute IS NOT NULL
MATCH (entity1:NewNode {title: line.Entity})
MATCH (entity2:NewNode {title: line.Attribute})
MERGE (entity1)-[rel:RELATION {type: line.AttributeName}]->(entity2);

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///attributes.csv" AS line
WITH line WHERE line.Entity IS NOT NULL AND line.Attribute IS NOT NULL
MATCH (entity1:NewNode {title: line.Entity})
MATCH (entity2:HudongItem {title: line.Attribute})
MERGE (entity1)-[rel:RELATION {type: line.AttributeName}]->(entity2);

// -----------------------------------------------------------------------------
// 5. Weather nodes and weather relations
// -----------------------------------------------------------------------------
USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///static_weather_list.csv" AS line
WITH line WHERE line.title IS NOT NULL AND trim(line.title) <> ""
MERGE (:Weather {title: line.title});

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///weather_plant.csv" AS line
WITH line WHERE line.Weather IS NOT NULL AND line.Plant IS NOT NULL
MATCH (weather:Weather {title: line.Weather})
MATCH (plant:HudongItem {title: line.Plant})
MERGE (weather)-[rel:Weather2Plant]->(plant)
SET rel.type = line.relation;

USING PERIODIC COMMIT 10000
LOAD CSV WITH HEADERS FROM "file:///city_weather.csv" AS line
WITH line WHERE line.city IS NOT NULL AND line.weather IS NOT NULL
MATCH (city)
WHERE city.title = line.city
MATCH (weather:Weather {title: line.weather})
MERGE (city)-[rel:CityWeather]->(weather)
SET rel.type = line.relation;

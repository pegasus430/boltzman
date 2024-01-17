CREATE or replace FUNCTION create_index(_index text, _table text, VARIADIC param_args text[]) RETURNS void AS
$$
declare 
   l_count integer;
begin
    select count(*) into l_count
    from pg_indexes
    where schemaname = 'public'
        and tablename = lower(_table)
        and indexname = lower(_index);

    if l_count = 0 then
        EXECUTE format('create index %I on %I (%s)', _index, _table, array_to_string($3,','));
    end if;
END;
$$
LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS object (
 id SERIAL PRIMARY KEY,
 parent_id integer ,
 className text,
 data  BYTEA
);

CREATE TABLE IF NOT EXISTS network (
 id SERIAL PRIMARY KEY,
 parent_id integer ,
 status text ,
 location text,
 className text,
 score REAL,
 lastTrainedDate int,
 modelFile text,
 data  BYTEA
);

CREATE TABLE IF NOT EXISTS dataport (
 id SERIAL PRIMARY KEY,
 network_id integer,
 size integer,
 timeseries_id int,
 aggregation_type int,
 data  BYTEA
);


CREATE TABLE IF NOT EXISTS timeSeries (
 id SERIAL PRIMARY KEY,
 parent_id integer ,
 timeSeriesName text NOT NULL,
 timeSeriesStamp int,
 timeSeriesClass text,
 timeSeriesCurrentValue REAL NOT NULL,
 UNIQUE(timeSeriesName,timeSeriesStamp)
);
-- CREATE INDEX IF NOT EXISTS idx_timeSeriesStamp
-- ON timeSeries (timeSeriesStamp);

CREATE TABLE IF NOT EXISTS option (
 id SERIAL PRIMARY KEY,
 parent_id integer ,
 optionName text NOT NULL,
 optionClass text,
 optionExchange text,
 optionDescription  BYTEA,
 UNIQUE(optionName,optionClass)
);


CREATE TABLE IF NOT EXISTS iex_symbols (
	id serial4 NOT NULL,
	symbol text NULL,
	exchange text NULL,
	exchangesuffix text NULL,
	exchangename text NULL,
	exchangesegment text NULL,
	exchangesegmentname text NULL,
	"name" text NULL,
	"date" text NULL,
	"type" text NULL,
	iexid text NULL,
	region text NULL,
	currency text NULL,
	isenabled text NULL,
	figi text NULL,
	cik text NULL,
	lei text NULL,
	active int4 NULL,
	data_quality_score int NULL,
	CONSTRAINT symbols_prkey PRIMARY KEY (id),
	CONSTRAINT symbols_symbol_exchange_key_const UNIQUE (symbol, exchange)
);
CREATE TABLE IF NOT EXISTS intakelog (
    id SERIAL PRIMARY KEY,
    symbol_id integer,
    pull_id text,
    status int, 
    startTimeStamp int,
    endTimeStamp int,
    source text,
    filePath text,
    error text,
    uniqueIdentifier text
);

CREATE TABLE IF NOT EXISTS marketCalendar (
 id SERIAL PRIMARY KEY,
 marketCode text ,
 timestamp int,
 description text,
 marketStatus int, -- 0 closed , 1 early closed
 countryCode text
);

CREATE TABLE IF NOT EXISTS service (
 id SERIAL PRIMARY KEY,
 uniqueId text, -- for service notifications this is the uuid , for networks or other db elements it is the db id
 timestamp int,
 serviceId text , -- service id, whichever service pushed it
 className text, -- class name of the service
 status text, -- service status online, time out, offline
 upsince int,
 networkCount int, 
 body  BYTEA 
);

CREATE TABLE IF NOT EXISTS notifications (
 id SERIAL PRIMARY KEY,
 sourceServiceId text, -- service that initiated te notification
 targetServiceId text, -- target service
 timestamp int,
 notification text , -- command to send to the service
 status int DEFAULT 0, -- status of the command 0: initial 1:pending 2: executed 3:failed
 error text, -- error message returned from service if status is 3 (failed)
 body  BYTEA -- reserved for extra parameters
);

CREATE TABLE IF NOT EXISTS predictions(
 id SERIAL PRIMARY KEY,
 source_network_id int,
 output_symbol text,
 prediction_time int,
 next_prediction_time int,
 matured_time int,
 score float,
 prediction_points BYTEA,
 real_values BYTEA,
 serviceId text , -- service id, whichever service pushed it
 className text -- class name of the service
);

CREATE TABLE IF NOT EXISTS resourceClass (
 id SERIAL PRIMARY KEY,
 classId text NOT NULL,
 className text NOT NULL,
 classDescription text NOT NULL,
 data BYTEA,
 UNIQUE(classId)
);

CREATE TABLE IF NOT EXISTS resourceSubClass (
 id SERIAL PRIMARY KEY,
 classId text NOT NULL,
 subClassId text NOT NULL,
 subClassName text NOT NULL,
 subClassDescription text NOT NULL,
 data BYTEA,
 UNIQUE(subClassId)
);

CREATE TABLE IF NOT EXISTS cluster (
 id SERIAL PRIMARY KEY,
 clusterId text NOT NULL,
 clusterType int NOT NULL,  -- 0: shared 1: dedicated to a single account
 registryTime int NOT NULL, -- registry time
 rootAccountId text NOT NULL, -- Account that has priviliges to modify cluster
 status int NOT NULL, --status 0:offline 1:initiating 2:online
 data BYTEA,
 UNIQUE(clusterId)
);

CREATE TABLE IF NOT EXISTS resource (
 id SERIAL PRIMARY KEY,
 resourceId text NOT NULL,
 resourceClassId text NOT NULL,
 resourceSubClassId text NOT NULL,
 clusterId text,
 resourceType int NOT NULL,  -- 0: shared 1: dedicated to a single account
 registryTime int NOT NULL, -- registry time
 status int NOT NULL, --status 0:offline 1:initiating 2:online
 data BYTEA,
 UNIQUE(resourceId)
);


CREATE TABLE IF NOT EXISTS resource_account (
 id SERIAL PRIMARY KEY,
 resourceId int NOT NULL,
 number int, -- unit number of logical resources , e.g number of containers. Only applies for shared resources
 -- for e.g: by looking at this number one can tell how many containers are running on a bare-metal computer for given account
 accountId int NOT NULL
);

select create_index('idx_resource_account_accountId', 'resource_account', 'accountId');


CREATE TABLE IF NOT EXISTS account (
 id SERIAL PRIMARY KEY,
 accountId text NOT NULL,
 accountOwner text NOT NULL,
 licenseType text NOT NULL,
 rootUserName text NOT NULL,
 rootUserPassword text NOT NULL,
 token  text NOT NULL,
 data BYTEA,
 UNIQUE(accountId)
);

CREATE TABLE IF NOT EXISTS project (
 id SERIAL PRIMARY KEY,
 projectId text NOT NULL,
 accountId text NOT NULL,
 name text NOT NULL,
 description TEXT,
 data BYTEA,
 UNIQUE(projectId)
);



CREATE TABLE IF NOT EXISTS token (
 id SERIAL PRIMARY KEY,
 accountid text NOT NULL,
 token text NOT NULL,
 expiresat int NOT NULL
);


CREATE TABLE IF NOT EXISTS application (
 id SERIAL PRIMARY KEY,
 uniqueid text NOT NULL,
 data BYTEA,
 status int NOT NULL,
 description TEXT,
 UNIQUE(uniqueid)
);

CREATE TABLE IF NOT EXISTS timeseries_definition ( -- 
 id SERIAL PRIMARY KEY,
 name TEXT NOT NULL,
 description TEXT,
 uniqueid text NOT NULL,
 dataCatalogId text NOT NULL, -- reference to data catalog node stored in app data field
 data BYTEA,
 status int NOT NULL DEFAULT 0, -- 0: Inactive 1:Active
 UNIQUE(uniqueid)
);

CREATE TABLE IF NOT EXISTS timeseries_project ( -- 
 id SERIAL PRIMARY KEY,
 uniqueid TEXT NOT NULL,
 projectid TEXT,
 timeseriesdefinitionid text NOT NULL,
 status int NOT NULL DEFAULT 0, -- 0: Inactive 1:Active
 UNIQUE(uniqueid),
 UNIQUE(projectid, timeseriesdefinitionid)
);

select create_index('idx_timeseries_project_timeseriesdefinitionid', 'timeseries_project', 'timeseriesdefinitionid');



select create_index('idx_timeseries_definition_dataCatalogId', 'timeseries_definition', 'dataCatalogId');

insert into account (accountId, accountOwner, licenseType, rootUserName,rootUserPassword, token)
VALUES ('001', 'Boltzman Inc', 'enterprise', 'root', 'abc123!', 'eyJhbGciOiJIUzI1NiJ9.eyJhY2NvdW50IjoiMTIzNDU2Nzg5MCIsIm5hbWUiOiJCb2x0em1hbiJ9.jx4ii6cyKShk2iNpfR9mdoi409BwIWaGRFM-CLM45f4');

select create_index('idx_service_notifications_uniqueId', 'serviceNotifications', 'uniqueId');
select create_index('idx_service_notifications_uniqueId', 'serviceNotifications', 'uniqueId');
select create_index('idx_service_notifications_uniqueId', 'intakelog', 'uniqueidentifier');
DELETE FROM network WHERE id > 0;

INSERT INTO application (
 uniqueid,
 data,
 status,
 description
)
VALUES(
	'3d7d6607-fd97-4da8-8c3c-3de3264506c0',
	'{
		"data_category_tree": {
		"310608be-1afa-45bf-9849-6d1e36c48368": {
			"name": "Financial Data",
			"description": "All Financial Data",
			"631a6cc2-835e-4b98-b92d-cac669367ff4": {
			"name": "US Markets",
			"description": "All All US Markets"
			}
		}
		}
  	}',
	0,
	'Boltzman Application Data'
)

drop table if exists plants;
drop table if exists zombies;



create table if not exists plants(
    id serial primary key,
    name varchar(50) not null,
    hp float not null,
    dmg int,
    dps FLOAT,
    fire_rate FLOAT,
    cost int,
    cd FLOAT
);

create table if not exists zombies (
    id serial primary key,
    name varchar(50) not null,
    hp int not null,
    dmg int not null,
    dps int not null,
    speed FLOAT NOT NULL,
    extra_health int not null
);



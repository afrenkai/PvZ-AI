insert into plants (name, hp, dmg, dps, fire_rate, cost, cd)
values
('Peashooter', 300, 20, 13.333, 1.425, 100, 7.5),
('Sunflower', 300, NULL, NULL, 24.25, 50, 7.5),
('Cherry Bomb', 'infinity'::numeric, 1800, 36, 1.2, 150, 50);

insert into zombies (name, hp, dmg, dps, speed, extra_health)
values
('Zombie', 181, 100, 100, 4.7, 89),
('Flag Zombie', 181, 100, 100, 3.7, 89),
('Conehead Zombie', 551, 100, 100, 4.7, 89);
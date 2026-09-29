CREATE TABLE `consents` (
	`id` text PRIMARY KEY NOT NULL,
	`profile_id` text NOT NULL,
	`type` text NOT NULL,
	`action` text NOT NULL,
	`version` text,
	`created_at` text DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')) NOT NULL,
	FOREIGN KEY (`profile_id`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE cascade,
	CONSTRAINT "consents_type_check" CHECK("consents"."type" IN ('processing', 'biometric', 'retain_images', 'training_data', 'research'))
);
--> statement-breakpoint
CREATE INDEX `consents_profile_type_idx` ON `consents` (`profile_id`,`type`);--> statement-breakpoint
CREATE TABLE `profiles` (
	`id` text PRIMARY KEY NOT NULL,
	`market` text NOT NULL,
	`locale` text NOT NULL,
	`birth_year` integer,
	`is_adult` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')) NOT NULL,
	CONSTRAINT "profiles_market_check" CHECK("profiles"."market" IN ('in', 'global'))
);

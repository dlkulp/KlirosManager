CREATE DATABASE kliros_manager;
CREATE TABLE `kliros_manager`.`user` (
	`UserID` int NOT NULL AUTO_INCREMENT,
	`Name` varchar(255) NOT NULL,
	`Email` varchar(255) NOT NULL,
	`JoinedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`UserType` enum('regular', 'moderator', 'admin') NOT NULL DEFAULT 'regular',
	PRIMARY KEY (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `kliros_manager`.`user` (`Name`, `Email`, `UserType`) VALUES
	('Local Owner', 'local@kliros.invalid', 'admin');

CREATE TABLE `kliros_manager`.`federated_credential` (
    `RowID` int NOT NULL AUTO_INCREMENT,
    `UserID` int NOT NULL,
    `Provider` varchar(255) NOT NULL,
	`ProfileID` varchar(255) NOT NULL,
	PRIMARY KEY (`RowID`),
	KEY `UserID` (`UserID`),
	CONSTRAINT `Federated_Credential_IBFK_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `kliros_manager`.`resource` (
	`id` int NOT NULL AUTO_INCREMENT,
	`DisplayName` varchar(255) DEFAULT NULL,
	`OriginalName` varchar(255) NOT NULL, 
	`MetaData` json, 
	`GroupID` int DEFAULT NULL, 
	`Source` varchar(255) DEFAULT NULL, 
	`UserID` int NOT NULL, 
	`Reviewed` boolean DEFAULT false, 
	`Public` boolean DEFAULT false, 
	`VisualHash` varchar(255), 
	`FileHash` varchar(64),
	`Hidden` boolean DEFAULT false,
	`DownloadCount` int DEFAULT 0, 
	PRIMARY KEY (`id`),
	KEY `UserID` (`UserID`),
	CONSTRAINT `resource_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
	CONSTRAINT `resource_ibfk_2` FOREIGN KEY (`GroupID`) REFERENCES `resource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `kliros_manager`.`favorites` (
	`UserID` int NOT NULL,
	`ResourceID` int NOT NULL,
	`FavoritedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (`UserID`, `ResourceID`),
	KEY `ResourceID` (`ResourceID`),
	CONSTRAINT `favorites_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
	CONSTRAINT `favorites_ibfk_2` FOREIGN KEY (`ResourceID`) REFERENCES `resource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `kliros_manager`.`metadata` (
	`id` int NOT NULL AUTO_INCREMENT, 
	`Name` varchar(255) NOT NULL, 
	`Type` varchar(255) NOT NULL,
	`Options` json DEFAULT NULL,
	`Core` boolean DEFAULT false,
	`Extracted` boolean DEFAULT false,
	`Searchable` boolean DEFAULT false,
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `kliros_manager`.`metadata`(`Name`,`Type`,`Options`,`Core`,`Extracted`,`Searchable`) values 
	('Composer','string', NULL, true, false, false),
	('Arranger','string', NULL, true, false, false),
	('Style','string', NULL, false, false, false),
	('Tone','string','["Tone 1","Tone 2","Tone 3","Tone 4","Tone 5","Tone 6","Tone 7","Tone 8"]', false, true, true),
	('Tradition','string','["Byzantine","Kievan","Obikhod","Znamenny","Georgian","Bulgarian","Byzantine","Serbian","Romanian","Carpatho-Rusyn","Ruthenian","Strochnoi"]', false, true, true),
	('Feast','string', NULL, false, false, true),
	('Feast Rank','string','["Ordinary","Double","Six Stichera","Great Doxology","Polyeleos","Vigil","Great Feast"]', false, false, true),
	('Service','string','["Vespers","Matins","Liturgy","Presanctified Liturgy","Compline","Hours","Midnight Office","Services of Need"]', false, true, true),
	('Part of Service','string', NULL, false, false, false),
	('Parts','number', '["Unison","One Part","Two Parts","Three Parts","Four Parts","Five+ Parts]', false, false, true),
	('Chorus Type','string','["male","female","mixed"]', false, true, true),
	('Voicing','string','["SATB","SA","SSA","SSAA"]', false, true, true),
	('Difficulty','string','["Difficulty 1","Difficulty 2","Difficulty 3","Difficulty 4","Difficulty 5"]', false, false, true),
	('Liturgical Date','date', NULL, false, false, true),
	('Copyright','string', NULL, false, false, false),
	('Language','string', '["English","Greek","Church Slavonic","Georgian","Bulgarian","Serbian","Romanian","Carpatho-Rusyn","Ruthenian"]', true, false, true),
	('English Title','string', NULL, false, false, false);

CREATE TABLE `kliros_manager`.`collection` (
	`id` int NOT NULL AUTO_INCREMENT, 
	`Name` varchar(255) NOT NULL, 
	`Public` boolean DEFAULT false, 
	`UserId` int DEFAULT NULL,
	PRIMARY KEY (`id`),
	KEY `UserID` (`UserId`),
	CONSTRAINT `collection_ibfk_1` FOREIGN KEY (`UserId`) REFERENCES `user` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `kliros_manager`.`collection_member` (
	`id` int NOT NULL AUTO_INCREMENT,
	`CollectionID` int NOT NULL,
	`ResourceID` int NOT NULL, 
	`Order` int DEFAULT NULL, 
	`Annotation` varchar(255) DEFAULT NULL,
	PRIMARY KEY (`id`),
	CONSTRAINT `collection_member_ibfk_1` FOREIGN KEY (`CollectionID`) REFERENCES `collection` (`id`),
	CONSTRAINT `collection_member_ibfk_2` FOREIGN KEY (`ResourceID`) REFERENCES `resource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

select * from kliros_manager.resource
delete from kliros_manager.resource
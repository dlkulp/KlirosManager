CREATE DATABASE kliros_manager;
CREATE TABLE `kliros_manager`.`user` (
	`UserID` int NOT NULL AUTO_INCREMENT,
	`Name` varchar(255) NOT NULL,
	`Email` varchar(255) NOT NULL,
	PRIMARY KEY (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
	`Hidden` boolean DEFAULT false,
	PRIMARY KEY (`id`),
	KEY `UserID` (`UserID`),
	CONSTRAINT `resource_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
	CONSTRAINT `resource_ibfk_2` FOREIGN KEY (`GroupID`) REFERENCES `resource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `kliros_manager`.`metadata` (
	`id` int NOT NULL AUTO_INCREMENT, 
	`Name` varchar(255) NOT NULL, 
	`Type` varchar(255) NOT NULL,
	`Options` json DEFAULT NULL,
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `kliros_manager`.`metadata`(`Name`,`Type`,`Options`) values 
	('Composer','string', NULL),
	('Style','string', NULL),
	('Tone','number','[1,2,3,4,5,6,7,8]'),
	('Tone Set','string','["Byzantine","Kievan","Obikhod","Znamenny","Georgian","Bulgarian","Byzantine","Serbian","Romanian","Carpatho-Rusyn","Ruthenian","Other"]'),
	('Feast','string', NULL),
	('Feast Rank','string','["Ordinary","Six Stichera","Great Doxology","Polyeleos","Vigil","Great"]'),
	('Part of Service','string', NULL),
	('Parts','number', NULL),
	('Chorus Type','string','["male","female","mixed"]'),
	('Difficulty','number','[1,2,3,4,5]'),
	('Liturgical Date','date', NULL),
	('Calendar Date','date', NULL),
	('Language','string', NULL),
	('Original Title','string', NULL);

CREATE TABLE `kliros_manager`.`collection` (
	`id` int NOT NULL AUTO_INCREMENT, 
	`Name` varchar(255) NOT NULL, 
	`Public` boolean DEFAULT false, 
	`UserId` int DEFAULT NULL,
	PRIMARY KEY (`id`),
	KEY `UserID` (`UserID`),
	CONSTRAINT `collection_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`)	
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
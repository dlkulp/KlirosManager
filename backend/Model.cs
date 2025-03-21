using System.ComponentModel.DataAnnotations;
using Microsoft.EntityFrameworkCore;

public class KlirosManagerContext : DbContext
{
	public DbSet<Collection> Collections {get; set;}
	public DbSet<CollectionMember> CollectionMembers {get; set;}
	public DbSet<FederatedCredential> FederatedCredentials {get; set;}
	public DbSet<Metadata> Metadata {get; set;}
	public DbSet<Resource> Resources {get; set;}
	public DbSet<User> Users {get; set;}
	public string conString {get; set;}

	public string DbPath { get; }

	protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
	{	
		optionsBuilder.UseMySQL(conString);
	}

	public KlirosManagerContext(string conString)
    {
        var folder = Environment.SpecialFolder.LocalApplicationData;
        var path = Environment.GetFolderPath(folder);
        DbPath = Path.Join(path, "klirosManager.db");
		this.conString = conString;
    }
}

public class Collection
{
	[Key]
	public required int ID {get; set;}
	public required string Name {get; set;}
	public bool Public {get; set;}
	public int? UserID {get; set;}
	public User? User {get; set;}
}

public class CollectionMember
{
	[Key]
	public required int ID {get; set;}
	public required int CollectionID {get; set;}
	public required int ResourceID {get; set;}
	public int? Order {get; set;}
	public string? Annotation {get; set;}
	public required Collection Collection {get; set;}
	public required Resource Resource {get; set;}
}

public class FederatedCredential
{
	[Key]
	public required int RowID {get; set;}
	public required int UserID {get; set;}
	public required string Provider {get; set;}
	public required string ProfileID {get; set;}
	public required User User {get; set;}
}

public class Metadata 
{
	[Key]
	public required int ID {get; set;}
	public required string Name {get; set;}
	public required string Type {get; set;}
	public string? Options {get; set;}
}

public class Resource
{
	[Key]
	public required int ID {get; set;}
	public string? DisplayName {get; set;}
	public required string OriginalName {get; set;}
	public required string Metadata {get; set;}
	public int? GroupID {get; set;}
	public string? Source {get; set;}
	public required int UserID {get; set;}
	public required bool Reviewed {get; set;}
	public required bool Public {get; set;}
	public required string PerceptualHash {get; set;}
	public required bool Hidden {get; set;}
	public required User User {get; set;}
}

public class User
{
	[Key]
	public required int UserID {get; set;}
	public required string Name {get; set;}
	public required string Email {get; set;}
}